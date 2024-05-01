from django.core.management.base import BaseCommand

from utils import debug, shopify, common

from vendor.models import Sync, Product

PROCESS = "Sync-Tag"


class Command(BaseCommand):
    help = f"Run {PROCESS}"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        with Processor() as processor:
            processor.tag()


class Processor:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def tag(self):

        syncs = Sync.objects.filter(type="Tag")

        def syncTag(index, sync):

            product = Product.objects.get(shopifyId=sync.productId)

            shopifyManager = shopify.ShopifyManager(
                product=product, thread=index)
            shopifyManager.updateProductTag()

            sync.delete()
            debug.log(
                PROCESS, f"Tag Sync for {sync.productId} has been completed.")

        common.thread(rows=syncs, function=syncTag)
