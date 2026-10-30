from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from inventory.models import Order, OrderItem, Product, ShippingBox

PRODUCTS = [
    ("Mug", "10", "8", "12", "0.500"),
    ("Paperback", "21", "14", "3", "0.400"),
    ("Desk Lamp", "40", "12", "12", "1.800"),
]
BOXES = [
    ("Small", "15", "12", "10", "3", "1.20"),
    ("Medium", "25", "20", "15", "8", "2.50"),
    ("Long", "45", "15", "15", "10", "3.80"),
    ("Large", "40", "30", "30", "20", "5.00"),
]
ORDERS = {
    "DEMO-1": [("Mug", 2)],
    "DEMO-2": [("Paperback", 3), ("Mug", 1)],
    "DEMO-3": [("Desk Lamp", 1)],
}


class Command(BaseCommand):
    help = "Create sample products, boxes and orders (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        products = {}
        for name, l, w, h, kg in PRODUCTS:
            products[name], _ = Product.objects.get_or_create(
                name=name,
                defaults=dict(length_cm=Decimal(l), width_cm=Decimal(w), height_cm=Decimal(h), weight_kg=Decimal(kg)),
            )
        for name, l, w, h, kg, cost in BOXES:
            ShippingBox.objects.get_or_create(
                name=name,
                defaults=dict(length_cm=Decimal(l), width_cm=Decimal(w), height_cm=Decimal(h),
                              max_weight_kg=Decimal(kg), cost=Decimal(cost)),
            )
        for ref, lines in ORDERS.items():
            order, _ = Order.objects.get_or_create(reference=ref)
            for product_name, qty in lines:
                OrderItem.objects.get_or_create(order=order, product=products[product_name], defaults={"quantity": qty})
        self.stdout.write("Demo data ready. Try: python manage.py recommend_box DEMO-1")
