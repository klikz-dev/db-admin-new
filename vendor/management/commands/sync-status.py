from django.core.management.base import BaseCommand
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils import debug, shopify

from vendor.models import Sync, Product, Image

PROCESS = "Sync-Status"


class Command(BaseCommand):
    help = f"Run {PROCESS}"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        with Processor() as processor:
            processor.status()
            processor.noImage()


class Processor:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def status(self):

        syncs = Sync.objects.filter(type="Status")

        def syncStatus(index, sync):
            product = Product.objects.get(shopifyId=sync.productId)

            try:
                Image.objects.get(product=product, position=1)
            except Image.DoesNotExist:
                debug.log(PROCESS, f"Image Not Found: {product.shopifyId}")
                product.published = False
                product.save()

            shopifyManager = shopify.ShopifyManager(thread=index)
            shopifyManager.updateProductStatus(
                productId=product.shopifyId, status=product.published)

        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_sync = {executor.submit(
                syncStatus, index, sync): sync for index, sync in enumerate(syncs)}

            for future in as_completed(future_to_sync):
                sync = future_to_sync[future]

                try:
                    future.result()
                    sync.delete()
                    debug.log(
                        PROCESS, f"Status Sync for {sync.productId} has been completed.")

                except Exception as e:
                    debug.warn(
                        PROCESS, f"Status Sync for {sync.productId} has been failed. {str(e)}")

    def noImage(self):
        shopifyManager = shopify.ShopifyManager()

        noImageProducts = Product.objects.exclude(
            images__position=1).filter(published=True)

        for product in noImageProducts:
            product.published = False
            product.save()

            try:
                shopifyManager.updateProductStatus(
                    productId=product.shopifyId, status=False)
                debug.log(
                    PROCESS, f"Set Status of Product to Inactive: {product.shopifyId}. Image missing.")

            except Exception as e:
                debug.warn(PROCESS, str(e))
                continue
