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
                product = Product.objects.get(shopifyId=productId)
            except Product.DoesNotExist:
                debug.warn(PROCESS, f"Product Not Found: {productId}")
                return

            try:
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

                # shopifyProduct = shopifyManager.requestAPI(
                #     method="GET", url=f"/products/{product.shopifyId}.json")
                # if 'product' not in shopifyProduct:
                #     product.delete()
                #     sync.delete()
                # else:
                #     for variantId in shopifyManager.variantsData.keys():
                #         shopifyManager.requestAPI(
                #             method="DELETE", url=f"/products/{product.shopifyId}/variants/{variantId}.json")

                #     base_variant_info = {
                #         "sku": product.sku,
                #         "cost": product.cost,
                #         "weight": product.weight,
                #         "weight_unit": "lb",
                #         "barcode": product.barcode,
                #         "inventory_management": None,
                #         "fulfillment_service": "manual",
                #     }

                #     variants_data = [
                #         {"title": "Consumer", "option1": "Consumer",
                #             "price": product.consumer},
                #         {"title": "Trade",
                #             "option1": "Trade", "price": product.trade},
                #         {"title": "Sample", "option1": "Sample",
                #             "price": product.sample, "cost": 0, "weight": 0},
                #         {"title": "Free Sample", "option1": "Free Sample",
                #             "price": 0, "cost": 0, "weight": 0}
                #     ]

                #     variants = [{**base_variant_info, **variant}
                #                 for variant in variants_data]

                #     productData = shopifyManager.productData
                #     productData['product']['variants'] = variants

                #     print(productData)

                #     try:

                #         metafieldsData = shopifyManager.requestAPI(
                #             method="GET", url=f"/products/{product.shopifyId}/metafields.json")

                #         for metafield in metafieldsData["metafields"]:
                #             shopifyManager.requestAPI(
                #                 method="DELETE", url=f"/metafields/{metafield['id']}.json")

                #         productRes = shopifyManager.requestAPI(
                #             method="PUT", url=f"/products/{product.shopifyId}.json", payload=shopifyManager.productData)

                #         for variant in productRes['product']['variants']:
                #             if variant['option1'] == "Consumer":
                #                 product.consumerId = variant['id']
                #             if variant['option1'] == "Trade":
                #                 product.tradeId = variant['id']
                #             if variant['option1'] == "Sample":
                #                 product.sampleId = variant['id']
                #             if variant['option1'] == "Free Sample":
                #                 product.freeSampleId = variant['id']

                #     except:
                #         product.delete()
                #         # sync.delete()

                #     product.save()
                #     sync.delete()

                return

            sync.delete()

        with ThreadPoolExecutor(max_workers=100) as executor:
            for index, sync in enumerate(syncs):
                executor.submit(syncContent, index, sync)
