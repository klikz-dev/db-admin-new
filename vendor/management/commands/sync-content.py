from django.core.management.base import BaseCommand
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils import debug, shopify

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

        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_sync = {executor.submit(
                syncContent, index, sync): sync for index, sync in enumerate(syncs)}

            for future in as_completed(future_to_sync):
                sync = future_to_sync[future]

                try:
                    future.result()
                    sync.delete()
                    debug.log(
                        PROCESS, f"Content Sync for {sync.productId} has been completed.")

                except Exception as e:
                    debug.warn(
                        PROCESS, f"Content Sync for {sync.productId} has been failed. {str(e)}")
