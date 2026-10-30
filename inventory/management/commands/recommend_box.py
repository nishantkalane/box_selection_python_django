import json

from django.core.management.base import BaseCommand, CommandError

from inventory.models import Order
from inventory.packing import OrderTooLarge
from inventory.views import recommendation_payload


class Command(BaseCommand):
    help = "Print the recommended shipping box for an order reference as JSON."

    def add_arguments(self, parser):
        parser.add_argument("reference")

    def handle(self, *args, **options):
        try:
            order = Order.objects.get(reference=options["reference"])
        except Order.DoesNotExist:
            raise CommandError(f"Order {options['reference']!r} does not exist.")
        try:
            payload = recommendation_payload(order)
        except OrderTooLarge as exc:
            raise CommandError(str(exc))
        self.stdout.write(json.dumps(payload, indent=2))
