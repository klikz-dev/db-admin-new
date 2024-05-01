from django.core.management.base import BaseCommand

from utils import debug, shopify, common

from vendor.models import Sync, Product

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

        def syncContent(index, sync):

            product = Product.objects.get(shopifyId=sync.productId)

            shopifyManager = shopify.ShopifyManager(
                product=product, thread=index)

            handle = shopifyManager.updateProduct()

            if handle:
                product.shopifyHandle = handle
                product.save()

            sync.delete()
            debug.log(
                PROCESS, f"Content Sync for {sync.productId} has been completed.")

        common.thread(rows=syncs, function=syncContent)
