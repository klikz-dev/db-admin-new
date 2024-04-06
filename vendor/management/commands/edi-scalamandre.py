from django.core.management.base import BaseCommand
from django.db.models import Max

from utils import debug, shopify

from vendor.models import Order

PROCESS = "EDI-Scalamandre"


class Command(BaseCommand):
    help = f"Run {PROCESS}"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "submit" in options['functions']:
            with Processor() as processor:
                processor.submit()


class Processor:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def submit(self):
        lastProcessed = Order.objects.filter(
            lineItems__product__manufacturer__brand="Scalamandre").aggregate(Max('shopifyId'))['shopifyId__max']

        print(lastProcessed)
