from django.core.management.base import BaseCommand
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

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

        total = len(syncs)

        # for index, sync in enumerate(tqdm(syncs)):
        def syncContent(index, sync):
            productId = sync.productId

            try:
                # if True:
                product = Product.objects.get(shopifyId=productId)
            except Product.DoesNotExist:
                debug.warn(PROCESS, f"Product Not Found: {productId}")
                return

            try:
                # if True:
                shopifyManager = shopify.ShopifyManager(
                    product=product, thread=index)

                handle = shopifyManager.updateProduct()

                if handle:
                    product.shopifyHandle = handle
                    product.save()
                    debug.log(
                        PROCESS, f"Updated Product {product.sku} -- (Progress: {index}/{total})")

            except Exception as e:
                debug.warn(PROCESS, str(e))
                return

            sync.delete()

        with ThreadPoolExecutor(max_workers=100) as executor:
            for index, sync in enumerate(syncs):
                executor.submit(syncContent, index, sync)
