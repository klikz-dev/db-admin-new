import environ
import requests
import json

from utils import debug, common

env = environ.Env()

SHOPIFY_API_BASE_URL = env('SHOPIFY_API_BASE_URL')
SHOPIFY_API_VERSION = env('SHOPIFY_API_VERSION')
SHOPIFY_API_TOKEN = env('SHOPIFY_API_TOKEN')
SHOPIFY_API_THREAD_TOKENS = env('SHOPIFY_API_THREAD_TOKENS')


VARIANT_OPTIONS = [
    "Consumer",
    "Trade",
    "Sample",
    "Free Sample"
]


class ShopifyManager:
    def __init__(self, product=None, thread=None):

        self.apiToken = SHOPIFY_API_TOKEN
        if thread != None:
            self.apiToken = SHOPIFY_API_THREAD_TOKENS.split(",")[thread % 10]

        if product:

            self.productId = product.shopifyId

            if product.type.parent == "Root":
                self.productType = product.type.name
            else:
                self.productType = product.type.parent

            self.productManufacturer = product.manufacturer.name

            self.variantsData = self.generateVariantsData(product=product)

            self.productMetafields = self.generateProductMetafields(
                product=product)

            self.productTags = self.generateProductTags(product=product)

            self.productData = self.generateProductData(product=product)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def requestAPI(self, method, url, payload={}):
        if method == "GET" or method == "DELETE":
            response = requests.request(
                method,
                f"{SHOPIFY_API_BASE_URL}/{SHOPIFY_API_VERSION}{url}",
                headers={
                    'X-Shopify-Access-Token': self.apiToken,
                }
            )
        else:
            response = requests.request(
                method,
                f"{SHOPIFY_API_BASE_URL}/{SHOPIFY_API_VERSION}{url}",
                headers={
                    'X-Shopify-Access-Token': self.apiToken,
                    'Content-Type': 'application/json'
                },
                json=payload
            )

        if response.status_code == 200:
            return json.loads(response.text)
        else:
            debug.warn(
                "Shopify", f"Shopify API Error for {url}. Error: {str(response.text)}")
            return {}

    def generateVariantsData(self, product):
        base_variant_info = {
            "sku": product.sku,
            "cost": product.cost,
            "weight": product.weight,
            "weight_unit": "lb",
            "barcode": product.barcode
        }

        variants_data = [
            {"id": product.consumerId, "title": "Consumer", "option1": "Consumer",
                "price": product.consumer, "compare_at_price": product.compare},
            {"id": product.tradeId, "title": "Trade",
                "option1": "Trade", "price": product.trade},
            {"id": product.sampleId, "title": "Sample", "option1": "Sample",
                "price": product.sample, "cost": 0, "weight": 5},
            {"id": product.freeSampleId, "title": "Free Sample", "option1": "Free Sample",
                "price": 0, "cost": 0, "weight": 5}
        ]

        return {variant['id']: {"variant": {**base_variant_info, **variant}} for variant in variants_data}

    def generateProductMetafields(self, product):
        keys = ["mpn", "pattern", "color", "collection", "width", "length", "height", "size", "uom", "minimum", "increment", "repeatH",
                "repeatV", "specs", "yardsPR", "content", "match", "material", "finish", "care", "country", "features", "usage", "disclaimer"]

        metafields = []
        for key in keys:
            value = getattr(product, key, None)

            if isinstance(value, list):
                value = json.dumps(value)

            metafields.append({
                "namespace": "custom",
                "key": key,
                "value": value
            })

        relatedProducts = common.getRelatedProducts(product=product)

        metafields.append({
            "namespace": "custom",
            "key": "related_products",
            "value": json.dumps(relatedProducts)
        })

        return metafields

    def generateProductTags(self, product):
        tags = []
        size = ''
        for tag in product.tags.all():
            tags.append(f"{tag.type}:{tag.name}")

            if tag.type == "Size":
                size = tag.name

        # Core value tagging
        tags.append(f"Type:{product.type.name}")
        tags.append(f"Brand:{product.manufacturer.brand}")

        # Rebuy tagging
        tags.append(
            f"Rebuy_Recommendation_{product.collection}_{product.color}")
        tags.append(f"Rebuy_Collection_{product.collection}")
        tags.append(f"Rebuy_Color_{product.color}")
        if product.type.name == "Rug" and size:
            tags.append(f"Rebuy_Rug_Size_{size}")
        if product.type.name == "Rug Pad" and size:
            tags.append(f"Rebuy_Rug_Pad_Size_{size}")

        return ",".join(tags)

    def generateProductData(self, product):
        return {
            "product": {
                "body_html": product.description,
                "options": [
                    {"name": "Type", "position": 1, "values": VARIANT_OPTIONS},
                ],
                "product_type": self.productType,
                "tags": self.productTags,
                "title": product.title.title(),
                "handle": common.toHandle(product.title),
                "vendor": self.productManufacturer,
                "metafields": self.productMetafields
            }
        }

    def updateProduct(self):
        for variantId in self.variantsData.keys():
            # Delete Variant Metafields
            metafieldsData = self.requestAPI(
                method="GET", url=f"/products/{self.productId}/variants/{variantId}/metafields.json")

            for metafield in metafieldsData["metafields"]:
                self.requestAPI(
                    method="DELETE", url=f"/metafields/{metafield['id']}.json")

            # Update Variant
            self.requestAPI(
                method="PUT", url=f"/variants/{variantId}.json", payload=self.variantsData[variantId])

        # Delete Product Metafields
        metafieldsData = self.requestAPI(
            method="GET", url=f"/products/{self.productId}/metafields.json")

        for metafield in metafieldsData["metafields"]:
            self.requestAPI(
                method="DELETE", url=f"/metafields/{metafield['id']}.json")

        # Update Product
        productData = self.requestAPI(
            method="PUT", url=f"/products/{self.productId}.json", payload=self.productData)

        return productData["product"]["handle"]

    def deleteProduct(self, productId):
        # Delete Product
        productData = self.requestAPI(
            method="DELETE", url=f"/products/{productId}.json")

        return productData
