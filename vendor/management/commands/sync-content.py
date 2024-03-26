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

        # for index, sync in enumerate(tqdm(syncs)):
        def syncContent(index, sync):
            productId = sync.productId

            try:
                product = Product.objects.get(shopifyId=productId)
            except Product.DoesNotExist:
                debug.warn(PROCESS, f"Product Not Found: {productId}")
                sync.delete()
                return

            try:
                shopifyManager = shopify.ShopifyManager(
                    product=product, thread=index)
                shopifyManager.updateProduct()

                debug.log(
                    PROCESS, f"{productId} Product updated: {product.title}")
            except Exception as e:
                debug.warn(PROCESS, str(e))
                sync.delete()
                return

            sync.delete()

        with ThreadPoolExecutor(max_workers=100) as executor:
            for index, sync in enumerate(syncs):
                executor.submit(syncContent, index, sync)
