from django.core.management.base import BaseCommand
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

from utils import debug, shopify

from vendor.models import Sync, Product

PROCESS = "Sync-Price"


class Command(BaseCommand):
    help = f"Run {PROCESS}"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        with Processor() as processor:
            processor.price()


class Processor:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def price(self):

        syncs = Sync.objects.filter(type="Price")

        # for index, sync in tqdm(syncs):
        def syncPrice(index, sync):
            productId = sync.productId

            try:
                product = Product.objects.get(shopifyId=productId)
            except Product.DoesNotExist:
                debug.warn(PROCESS, f"Product Not Found: {productId}")
                sync.delete()
                return

            try:
                shopifyManager = shopify.ShopifyManager(thread=index)
                shopifyManager.updateProductPrice(product=product)

                debug.log(
                    PROCESS, f"{productId} Price updated: {product.consumer} / {product.trade} / {product.cost}")
            except Exception as e:
                debug.warn(PROCESS, str(e))
                sync.delete()
                return

            sync.delete()

        with ThreadPoolExecutor(max_workers=100) as executor:
            for index, sync in enumerate(syncs):
                executor.submit(syncPrice, index, sync)
