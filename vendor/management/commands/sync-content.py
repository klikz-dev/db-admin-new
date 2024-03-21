from django.core.management.base import BaseCommand
from tqdm import tqdm

from utils import debug, shopify

from vendor.models import Sync, Product, Image

PROCESS = "Sync-Content"


class Command(BaseCommand):
    help = f"Run {PROCESS}"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        with Processor() as processor:
            processor.content()


class Processor:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def content(self):
        syncs = Sync.objects.filter(type="Content")

        for sync in tqdm(syncs):
            pass
