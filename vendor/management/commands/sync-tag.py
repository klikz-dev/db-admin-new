from django.core.management.base import BaseCommand
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils import debug, shopify

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

        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_sync = {executor.submit(
                syncTag, index, sync): sync for index, sync in enumerate(syncs)}

            for future in as_completed(future_to_sync):
                sync = future_to_sync[future]

                try:
                    future.result()
                    sync.delete()
                    debug.log(
                        PROCESS, f"Tag Sync for {sync.productId} has been completed.")

                except Exception as e:
                    debug.warn(
                        PROCESS, f"Tag Sync for {sync.productId} has been failed. {str(e)}")
