from django.core.management.base import BaseCommand

from concurrent.futures import ThreadPoolExecutor
import time

from utils import debug, shopify

from vendor.models import Sync, Product, Image

PROCESS = "Status Sync"


class Command(BaseCommand):
    help = f"Run {PROCESS} processor"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        while True:
            with Processor() as processor:
                processor.status()
                processor.noImage()

            print("Finished process. Waiting for next run.")
            time.sleep(3600)


class Processor:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def status(self):
        syncs = Sync.objects.filter(type="Status")

        def updateStatus(index, sync):
            productId = sync.productId
            sync.delete()

            try:
                product = Product.objects.get(shopifyId=productId)
            except Product.DoesNotExist:
                debug.warn(PROCESS, f"Product Not Found: {productId}")
                return

            try:
                Image.objects.get(product=product, position=1)
            except Image.DoesNotExist:
                debug.warn(PROCESS, f"Image Not Found: {productId}")
                product.published = False
                product.save()

            try:
                shopifyManager = shopify.ShopifyManager(thread=index)
                shopifyManager.updateProductStatus(
                    productId=productId, status=product.published)

                debug.log(PROCESS, f"Updated Status of Product: {productId}")
            except Exception as e:
                debug.warn(PROCESS, str(e))
                return

        with ThreadPoolExecutor(max_workers=20) as executor:
            for index, sync in enumerate(syncs):
                executor.submit(updateStatus, index, sync)

    def noImage(self):

        noImageProducts = Product.objects.exclude(
            images__position=1).filter(published=True)

        for product in noImageProducts:
            product.published = False
            product.save()

            try:
                shopifyManager = shopify.ShopifyManager()
                shopifyManager.updateProductStatus(
                    productId=product.shopifyId, status=False)

                debug.log(
                    PROCESS, f"Set Status of Product to Inactive: {product.shopifyId}. Image missing.")
            except:
                return
