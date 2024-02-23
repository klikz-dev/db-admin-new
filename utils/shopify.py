import environ
import requests
import json

from vendor.models import Product, Sync
from utils import debug, const

env = environ.Env()

SHOPIFY_API_BASE_URL = env('SHOPIFY_API_BASE_URL')
SHOPIFY_API_VERSION = env('SHOPIFY_API_VERSION')
SHOPIFY_API_KEY = env('SHOPIFY_API_KEY')
SHOPIFY_API_SEC = env('SHOPIFY_API_SEC')
SHOPIFY_API_TOKEN = env('SHOPIFY_API_TOKEN')


class ShopifyManager:
    def __init__(self):
        self.API_HEADER = {
            'X-Shopify-Access-Token': SHOPIFY_API_TOKEN,
            'Content-Type': 'application/json'
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def requestAPI(self, method, url, payload):
        url = f"{SHOPIFY_API_BASE_URL}/{SHOPIFY_API_VERSION}"

        response = requests.request(
            method, url, headers=self.API_HEADER, data=payload)

        return response


class Productmanager:
    def __init__(self, product):
        self.metafields = [
            {
                "namespace": "shopify--facts.mpn",
                "key": ".mpn",
                "value": "product.mpn",
                "type": "single_line_text_field"
            }
        ]

        self.productData = {
            "body_html": product.description,
            "options": [
                {"name": "Type", "position": 1, "values": [
                    "Consumer", "Trade", "Sample", "Free Sample"]},
            ],
            "product_type": product.type,
            "tags": ",".join(product.tags),
            "title": product.title.title(),
            "handle": product.shopifyHandle,
            "vendor": product.manufacturer,
            "metafields": self.metafields
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def updateProduct(product):
    shopifyManager = ShopifyManager()
    productManager = Productmanager(product=product)

    response = shopifyManager.requestAPI(
        method="PUT", url=f"/products/{product.shopifyId}.json", payload=productManager.productData)

    if response.status == 200:
        data = json.loads(response.text)
        return data["product"]["handle"]
    else:
        debug.warn(
            "Shopify", f"Product Update Error for {product.shopifyId}. Error: {str(response.error)}")
