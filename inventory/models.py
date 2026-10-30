from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=120, unique=True)
    length_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    width_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    height_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    weight_kg = models.DecimalField(max_digits=8, decimal_places=3, validators=[MinValueValidator(Decimal("0.001"))])

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(length_cm__gte=Decimal("0.01")), name="product_length_positive"),
            models.CheckConstraint(check=models.Q(width_cm__gte=Decimal("0.01")), name="product_width_positive"),
            models.CheckConstraint(check=models.Q(height_cm__gte=Decimal("0.01")), name="product_height_positive"),
            models.CheckConstraint(check=models.Q(weight_kg__gte=Decimal("0.001")), name="product_weight_positive"),
        ]

    def __str__(self):
        return self.name


class ShippingBox(models.Model):
    name = models.CharField(max_length=120, unique=True)
    length_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    width_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    height_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    max_weight_kg = models.DecimalField(max_digits=8, decimal_places=3, validators=[MinValueValidator(Decimal("0.001"))])
    cost = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(length_cm__gte=Decimal("0.01")), name="box_length_positive"),
            models.CheckConstraint(check=models.Q(width_cm__gte=Decimal("0.01")), name="box_width_positive"),
            models.CheckConstraint(check=models.Q(height_cm__gte=Decimal("0.01")), name="box_height_positive"),
            models.CheckConstraint(check=models.Q(max_weight_kg__gte=Decimal("0.001")), name="box_weight_positive"),
            models.CheckConstraint(check=models.Q(cost__gte=Decimal("0.00")), name="box_cost_nonnegative"),
        ]

    def __str__(self):
        return self.name


class Order(models.Model):
    reference = models.CharField(max_length=40, unique=True)
    products = models.ManyToManyField(Product, through="OrderItem", related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.reference


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["order", "product"], name="unique_product_per_order"),
            models.CheckConstraint(check=models.Q(quantity__gte=1), name="order_item_quantity_positive"),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product}"
