import environ
import requests
import json

from utils import debug, common
from vendor.models import Product

env = environ.Env()

SHOPIFY_API_BASE_URL = env('SHOPIFY_API_BASE_URL')
SHOPIFY_API_VERSION = env('SHOPIFY_API_VERSION')
SHOPIFY_API_KEY = env('SHOPIFY_API_KEY')
SHOPIFY_API_SEC = env('SHOPIFY_API_SEC')
SHOPIFY_API_TOKEN = env('SHOPIFY_API_TOKEN')


class ShopifyManager:
    def __init__(self):
        pass

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
                    'X-Shopify-Access-Token': SHOPIFY_API_TOKEN,
                }
            )
        else:
            response = requests.request(
                method,
                f"{SHOPIFY_API_BASE_URL}/{SHOPIFY_API_VERSION}{url}",
                headers={
                    'X-Shopify-Access-Token': SHOPIFY_API_TOKEN,
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


class Productmanager:
    def __init__(self, product):
        self.tags = []

        if product.type.parent == "Root":
            self.type = product.type.name
        else:
            self.type = product.type.parent

        self.manufacturer = product.manufacturer.name

        self.handle = common.toHandle(product.title)

        self.variantOptions = [
            "Consumer",
            "Trade",
            "Sample",
            "Free Sample"
        ]

        self.variantsData = self.getVariantsData(product)
        self.productMetafields = self.getProductMetafields(product)
        self.productData = self.getProductData(product)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def getVariantsData(self, product):
        base_variant_info = {
            "sku": product.sku,
            "cost": product.cost,
            "weight": product.weight,
            "weight_unit": "lb",
            "barcode": product.barcode
        }

        variants_data = [
            {"title": "Consumer", "option1": "Consumer",
                "price": product.consumer, "compare_at_price": product.compare},
            {"title": "Trade", "option1": "Trade", "price": product.trade},
            {"title": "Sample", "option1": "Sample",
                "price": product.sample, "cost": 0, "weight": 5},
            {"title": "Free Sample", "option1": "Free Sample",
                "price": 0, "cost": 0, "weight": 5}
        ]

        return [{**base_variant_info, **variant} for variant in variants_data]

    def getProductMetafields(self, product):
        keys = ["mpn", "pattern", "color", "collection", "width", "length", "height", "size", "repeatH", "repeatV", "specs", "yardsPR",
                "content", "match", "material", "finish", "care", "country", "features", "usage", "disclaimer"]

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

    def getProductData(self, product):
        return {
            "product": {
                "body_html": product.description,
                "options": [
                    {"name": "Type", "position": 1, "values": [
                        "Consumer", "Trade", "Sample", "Free Sample"]},
                ],
                "product_type": self.type,
                "tags": ",".join(self.tags),
                "title": product.title.title(),
                "handle": self.handle,
                "vendor": self.manufacturer,
                "metafields": self.productMetafields
            }
        }


def getProductMetafields(product):
    shopifyManager = ShopifyManager()

    return shopifyManager.requestAPI(
        method="GET", url=f"/products/{product.shopifyId}/metafields.json")


def deleteMetafields(product):
    shopifyManager = ShopifyManager()

    metafieldsData = getProductMetafields(product)
    for metafield in metafieldsData["metafields"]:
        shopifyManager.requestAPI(
            method="DELETE", url=f"/metafields/{metafield['id']}.json")


def updateProduct(product):
    shopifyManager = ShopifyManager()
    productManager = Productmanager(product=product)

    deleteMetafields(product)

    productData = shopifyManager.requestAPI(
        method="PUT", url=f"/products/{product.shopifyId}.json", payload=productManager.productData)

    return productData["product"]["handle"]
