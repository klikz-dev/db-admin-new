from django.core.management.base import BaseCommand
from tqdm import tqdm

from utils import debug, shopify

from vendor.models import Sync, Product, Image

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
        shopifyManager = shopify.ShopifyManager()

        syncs = Sync.objects.filter(type="Price")

        for sync in tqdm(syncs):
            productId = sync.productId
            sync.delete()

            try:
                product = Product.objects.get(shopifyId=productId)
            except Product.DoesNotExist:
                debug.warn(PROCESS, f"Product Not Found: {productId}")
                return

            try:
                shopifyManager.updateProductPrice(product=product)

                debug.log(
                    PROCESS, f"{productId} Price updated: {product.consumer} / {product.trade} / {product.cost}")
            except Exception as e:
                debug.warn(PROCESS, str(e))
                return
