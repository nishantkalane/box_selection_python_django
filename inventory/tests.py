from decimal import Decimal

from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings

from .models import Order, OrderItem, Product, ShippingBox
from .packing import _overlaps, _pack, recommend_box


class RecommendBoxTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name="Mug", length_cm=10, width_cm=8, height_cm=12, weight_kg="0.500")
        self.order = Order.objects.create(reference="ORD-1")
        OrderItem.objects.create(order=self.order, product=self.product, quantity=1)

    def box(self, name, dims, weight="10", cost="5", active=True):
        return ShippingBox.objects.create(name=name, length_cm=dims[0], width_cm=dims[1], height_cm=dims[2], max_weight_kg=weight, cost=cost, active=active)

    def test_chooses_lowest_cost_box_and_allows_rotation(self):
        self.box("Large cheap", (20, 20, 20), cost="2")
        chosen = self.box("Rotated snug", (12, 10, 8), cost="1")
        result = recommend_box(self.order)
        self.assertEqual(result.box, chosen)
        self.assertEqual(result.total_weight_kg, Decimal("0.500"))

    def test_excludes_box_that_cannot_fit_item_even_if_volume_is_enough(self):
        self.box("Long and thin", (30, 3, 3), cost="0")
        fitting = self.box("Fits", (12, 10, 8), cost="4")
        self.assertEqual(recommend_box(self.order).box, fitting)

    def test_respects_weight_capacity(self):
        self.product.weight_kg = Decimal("2.000")
        self.product.save()
        self.box("Too light", (20, 20, 20), weight="1")
        self.assertIsNone(recommend_box(self.order))

    def test_respects_quantity_and_total_volume(self):
        self.order.items.update(quantity=3)
        self.box("Small", (12, 10, 8), cost="1")
        large = self.box("Large", (20, 20, 20), cost="2")
        self.assertEqual(recommend_box(self.order).box, large)

    def test_ignores_inactive_boxes(self):
        self.box("Inactive", (12, 10, 8), active=False)
        self.assertIsNone(recommend_box(self.order))

    def test_empty_order_has_no_recommendation(self):
        empty = Order.objects.create(reference="EMPTY")
        self.assertIsNone(recommend_box(empty))

    def test_returns_none_when_no_box_exists(self):
        self.assertIsNone(recommend_box(self.order))

    def test_model_validation_rejects_non_positive_measurements(self):
        invalid_product = Product(
            name="Invalid",
            length_cm="0",
            width_cm="8",
            height_cm="12",
            weight_kg="0",
        )
        with self.assertRaises(ValidationError):
            invalid_product.full_clean()

    def test_model_validation_rejects_zero_quantity(self):
        item = OrderItem(order=self.order, product=self.product, quantity=0)
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_database_rejects_invalid_product_measurement(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Product.objects.create(name="Invalid DB Product", length_cm=0, width_cm=8, height_cm=12, weight_kg="0.500")

    def test_database_rejects_negative_box_cost(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ShippingBox.objects.create(name="Invalid DB Box", length_cm=10, width_cm=10, height_cm=10, max_weight_kg=1, cost="-1")

    def test_database_rejects_zero_order_quantity(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OrderItem.objects.create(order=self.order, product=self.product, quantity=0)


from django.core.management import call_command
from io import StringIO
import json

from .packing import MAX_UNITS, OrderTooLarge, can_pack


class PackingTests(TestCase):
    def make_order(self, ref, dims, qty, weight="0.100"):
        product = Product.objects.create(name=f"P-{ref}", length_cm=dims[0], width_cm=dims[1], height_cm=dims[2], weight_kg=weight)
        order = Order.objects.create(reference=ref)
        OrderItem.objects.create(order=order, product=product, quantity=qty)
        return order

    def box(self, name, dims, cost="5", weight="50"):
        return ShippingBox.objects.create(name=name, length_cm=dims[0], width_cm=dims[1], height_cm=dims[2], max_weight_kg=weight, cost=cost)

    def test_rejects_box_that_passes_volume_and_per_item_checks_but_cannot_pack(self):
        # Two 6cm cubes: total 432 < 1000 and each fits a 10cm cube, but 6+6 > 10 on every axis.
        order = self.make_order("CUBES", (6, 6, 6), 2)
        self.box("Cube10", (10, 10, 10), cost="1")
        bigger = self.box("Cube12", (12, 12, 12), cost="3")
        self.assertEqual(recommend_box(order).box, bigger)

    def test_exact_fit_is_accepted(self):
        order = self.make_order("EXACT", (5, 5, 5), 8)
        box = self.box("Cube10", (10, 10, 10))
        self.assertEqual(recommend_box(order).box, box)

    def test_one_unit_over_exact_fit_is_rejected(self):
        order = self.make_order("OVER", (5, 5, 5), 9)
        self.box("Cube10", (10, 10, 10))
        self.assertIsNone(recommend_box(order))

    def test_mixed_products_pack_together(self):
        order = self.make_order("MIX", (10, 10, 5), 1)
        flat = Product.objects.create(name="Flat", length_cm=10, width_cm=10, height_cm=5, weight_kg="0.100")
        OrderItem.objects.create(order=order, product=flat, quantity=1)
        box = self.box("Stack", (10, 10, 10))
        self.assertEqual(recommend_box(order).box, box)

    def test_tie_on_cost_prefers_smaller_volume(self):
        order = self.make_order("TIE", (5, 5, 5), 1)
        self.box("Big", (20, 20, 20), cost="2")
        small = self.box("Small", (6, 6, 6), cost="2")
        self.assertEqual(recommend_box(order).box, small)

    def test_can_pack_helper(self):
        box = ShippingBox(length_cm=10, width_cm=10, height_cm=10)
        self.assertTrue(can_pack([(Decimal(5),) * 3] * 8, box))
        self.assertFalse(can_pack([(Decimal(6),) * 3] * 2, box))

    def test_order_over_unit_cap_raises(self):
        order = self.make_order("HUGE", (1, 1, 1), MAX_UNITS + 1)
        with self.assertRaises(OrderTooLarge):
            recommend_box(order)


class ApiTests(TestCase):
    def setUp(self):
        if settings.BOX_API_TOKEN:
            self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {settings.BOX_API_TOKEN}"
        product = Product.objects.create(name="Mug", length_cm=10, width_cm=8, height_cm=12, weight_kg="0.500")
        self.order = Order.objects.create(reference="ORD-API")
        OrderItem.objects.create(order=self.order, product=product, quantity=2)
        ShippingBox.objects.create(name="Medium", length_cm=30, width_cm=30, height_cm=30, max_weight_kg=10, cost="3.50")

    def test_endpoint_returns_recommended_box(self):
        data = self.client.get("/orders/ORD-API/box/").json()
        self.assertEqual(data["box"]["name"], "Medium")
        self.assertEqual(data["total_weight_kg"], "1.000")

    def test_endpoint_returns_null_box_when_nothing_fits(self):
        ShippingBox.objects.all().delete()
        self.assertIsNone(self.client.get("/orders/ORD-API/box/").json()["box"])

    def test_endpoint_404_for_unknown_order(self):
        self.assertEqual(self.client.get("/orders/NOPE/box/").status_code, 404)

    def test_endpoint_rejects_non_get(self):
        self.assertEqual(self.client.post("/orders/ORD-API/box/").status_code, 405)

    @override_settings(BOX_API_TOKEN="test-token")
    def test_endpoint_requires_token_when_configured(self):
        response = Client().get("/orders/ORD-API/box/")
        self.assertEqual(response.status_code, 401)

    @override_settings(BOX_API_TOKEN="test-token")
    def test_endpoint_accepts_valid_bearer_token(self):
        client = Client(HTTP_AUTHORIZATION="Bearer test-token")
        response = client.get("/orders/ORD-API/box/")
        self.assertEqual(response.status_code, 200)

    def test_management_command_prints_json(self):
        out = StringIO()
        call_command("recommend_box", "ORD-API", stdout=out)
        self.assertEqual(json.loads(out.getvalue())["box"]["name"], "Medium")


class PackingSoundnessTests(TestCase):
    def test_random_layouts_are_in_bounds_non_overlapping_and_complete(self):
        """Whenever _pack claims success, the layout must be physically valid."""
        import itertools
        import random

        rng = random.Random(1)
        packed = 0
        for _ in range(1500):
            box = tuple(Decimal(rng.randint(2, 15)) for _ in range(3))
            units = [tuple(Decimal(rng.randint(1, 8)) for _ in range(3)) for _ in range(rng.randint(1, 8))]
            placements = _pack(units, box)
            if placements is None:
                continue
            packed += 1
            for x, y, z, l, w, h in placements:
                self.assertTrue(x >= 0 and y >= 0 and z >= 0)
                self.assertTrue(x + l <= box[0] and y + w <= box[1] and z + h <= box[2])
            for a, b in itertools.combinations(placements, 2):
                self.assertFalse(_overlaps(a, b))
            self.assertEqual(
                sorted(sorted((l, w, h)) for *_, l, w, h in placements),
                sorted(sorted(u) for u in units),
            )
        self.assertGreater(packed, 100)


class SeedDemoTests(TestCase):
    def test_seed_demo_is_idempotent_and_recommends(self):
        from io import StringIO

        from django.core.management import call_command

        call_command("seed_demo", stdout=StringIO())
        call_command("seed_demo", stdout=StringIO())
        self.assertEqual(Order.objects.count(), 3)
        self.assertEqual(recommend_box(Order.objects.get(reference="DEMO-1")).box.name, "Medium")
        self.assertEqual(recommend_box(Order.objects.get(reference="DEMO-3")).box.name, "Long")
