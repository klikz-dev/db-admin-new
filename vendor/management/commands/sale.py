from django.core.management.base import BaseCommand
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

from utils import debug, shopify

from vendor.models import Sync, Product

PROCESS = "Sale-Scheduler"

schedules = [
    {
        "brand": "Surya",
        "discount": 15,
        "start": "2025-01-01 00:00",
        "end": "2025-03-31 23:59",
        "filter": {
            "collection__in": [
                "Adalei",
                "Didim",
                "Harare"
            ]
        }
    },
    {
        "brand": "York",
        "discount": 10,
        "start": "2024-03-01 00:00",
        "end": "2024-04-30 23:59",
        "filter": "all"
    }
]


class Command(BaseCommand):
    help = f"Run {PROCESS}"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        with Processor() as processor:
            processor.schedule()


class Processor:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def schedule(self):

        pass
