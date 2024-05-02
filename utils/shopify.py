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

PROCESS = "Shopify"


class ShopifyManager:
    def __init__(self, product=None, thread=None):

        self.apiToken = SHOPIFY_API_TOKEN
        if thread != None:
            self.apiToken = SHOPIFY_API_THREAD_TOKENS.split(",")[thread % 10]

        if product:

            self.productId = product.shopifyId

            if product.type.parent == "Root":
                self.type = product.type.name
                self.subType = ""
            else:
                self.type = product.type.parent
                self.subType = product.type.name

            self.brand = product.manufacturer.brand
            self.manufacturer = product.manufacturer.name

            self.existingVariantsData = self.generateVariantsData(
                product=product, new=False)
            self.newVariantsData = self.generateVariantsData(
                product=product, new=True)

            self.metafields = self.generateMetafields(product=product)

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

        if response.status_code == 200 or response.status_code == 201:
            return json.loads(response.text)
        else:
            debug.warn(
                PROCESS, f"Shopify API Error for {url}. Error: {str(response.text)}")
            return {}

    def generateVariantsData(self, product, new=False):
        base_variant_info = {
            "sku": product.sku,
            "cost": product.cost,
            "weight": product.weight,
            "weight_unit": "lb",
            "barcode": product.upc,
            "inventory_management": None,
            "fulfillment_service": "manual",
        }

        if new:
            variants_data = [
                {"title": "Consumer", "option1": "Consumer",
                    "price": product.consumer},
                {"title": "Trade", "option1": "Trade", "price": product.trade},
                {"title": "Sample", "option1": "Sample",
                    "price": product.sample, "cost": 0, "weight": 0},
                {"title": "Free Sample", "option1": "Free Sample",
                    "price": 0, "cost": 0, "weight": 0}
            ]
            return [{**base_variant_info, **variant} for variant in variants_data]
        else:
            variants_data = [
                {"id": product.consumerId, "title": "Consumer", "option1": "Consumer",
                    "price": product.consumer, "compare_at_price": product.compare},
                {"id": product.tradeId, "title": "Trade",
                    "option1": "Trade", "price": product.trade},
                {"id": product.sampleId, "title": "Sample", "option1": "Sample",
                    "price": product.sample, "cost": 0, "weight": 0},
                {"id": product.freeSampleId, "title": "Free Sample", "option1": "Free Sample",
                    "price": 0, "cost": 0, "weight": 0}
            ]
            return {variant['id']: {"variant": {**base_variant_info, **variant}} for variant in variants_data}

    def generateMetafields(self, product):
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
        size = None

        # Core Tagging
        tags.append(f"Brand:{self.brand}")
        tags.append(f"Type:{self.type}")

        tags.append(f"Manufacturer:{self.manufacturer} {self.type}")

        if self.subType:
            tags.append(f"Subtype:{self.subType}")

        # Attribute Tagging
        for tag in product.tags.all():
            tags.append(f"{tag.type}:{tag.name}")

            if tag.type == "Category":
                tags.append(f"Subcategory:{tag.name}")

            if tag.type == "Size":
                size = tag.name

        # Rebuy Tagging
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
                "product_type": self.type,
                "tags": self.productTags,
                "title": product.title.title(),
                "handle": common.toHandle(product.title),
                "vendor": self.manufacturer,
                "metafields": self.metafields
            }
        }

    def updateVariant(self, variantId):
        variantData = self.requestAPI(
            method="PUT", url=f"/variants/{variantId}.json", payload=self.existingVariantsData[variantId])

        return variantData

    def getMetafields(self):
        metafieldsData = self.requestAPI(
            method="GET", url=f"/products/{self.productId}/metafields.json")

        return metafieldsData["metafields"]

    def deleteMetafield(self, metafieldId):
        self.requestAPI(
            method="DELETE", url=f"/metafields/{metafieldId}.json")

        return True

    def createProduct(self):
        # Create Product
        self.productData['product']['variants'] = self.newVariantsData

        productData = self.requestAPI(
            method="POST", url=f"/products.json", payload=self.productData)

        return productData["product"]

    def updateProduct(self):
        # Update Variants
        for variantId in self.existingVariantsData.keys():
            self.updateVariant(variantId=variantId)

        # Delete Metafields
        metafields = self.getMetafields()
        for metafield in metafields:
            self.deleteMetafield(metafieldId=metafield['id'])

        # Update Product
        productData = self.requestAPI(
            method="PUT", url=f"/products/{self.productId}.json", payload=self.productData)

        return productData["product"]["handle"]

    def updateProductStatus(self, productId, status):
        productData = self.requestAPI(
            method="PUT",
            url=f"/products/{productId}.json",
            payload={
                "product":
                {
                    'id': productId,
                    'published': status,
                    'status': 'active'
                }
            }
        )

        return productData["product"]["handle"]

    def updateProductPrice(self, product):
        consumerVariant = {
            'id': product.consumerId,
            'cost': product.cost,
            'price': product.consumer,
            'compare_at_price': product.compare
        }
        self.requestAPI(
            method="PUT", url=f"/variants/{product.consumerId}.json", payload={"variant": consumerVariant})

        tradeVariant = {
            'id': product.tradeId,
            'cost': product.cost,
            'price': product.trade,
        }
        self.requestAPI(
            method="PUT", url=f"/variants/{product.tradeId}.json", payload={"variant": tradeVariant})

        return True

    def updateProductTag(self):
        # Check exiting tags
        tagsData = self.requestAPI(
            method="GET",
            url=f"/products/{self.productId}.json?fields=tags",
        )

        if "Block:Change" in tagsData['product']['tags']:
            debug.log(PROCESS, f"Change is blocked for {self.productId}")
            return

        productData = self.requestAPI(
            method="PUT",
            url=f"/products/{self.productId}.json",
            payload={
                "product": {
                    'id': self.productId,
                    "tags": self.productTags,
                }
            }
        )

        return productData["product"]["handle"]

    def deleteProduct(self, productId):
        productData = self.requestAPI(
            method="DELETE", url=f"/products/{productId}.json")

        return productData

    def getOrders(self, lastOrderId):
        ordersData = self.requestAPI(
            method="GET", url=f"/orders.json?since_id={lastOrderId}&status=any&limit=250")

        if 'orders' in ordersData:
            return ordersData['orders']
        else:
            return []

    def getOrder(self, orderId):
        ordersData = self.requestAPI(
            method="GET", url=f"/orders/{orderId}.json")

        if 'order' in ordersData:
            return ordersData['order']
        else:
            return {}

    def updateOrder(self, orderId, payload):
        ordersData = self.requestAPI(
            method="PUT", url=f"/orders/{orderId}.json", payload=payload)

        if 'order' in ordersData:
            return ordersData['order']
        else:
            return {}

    def deleteImage(self, productId, imageId):
        self.requestAPI(
            method="DELETE", url=f"/products/{productId}/images/{imageId}.json")

    def uploadImage(self, productId, position, link, alt):
        imageData = self.requestAPI(
            method="POST",
            url=f"/products/{productId}/images.json",
            payload={"image": {"position": position, "src": link, "alt": alt}}
        )

        return imageData['image']

    def getFulfillment(self, orderId):
        fulfillmentOrdersData = self.requestAPI(
            method="GET", url=f"/orders/{orderId}/fulfillment_orders.json")
        fulfillmentOrders = fulfillmentOrdersData['fulfillment_orders']

        if len(fulfillmentOrders) > 0:
            return fulfillmentOrders[0]
        else:
            return None

    def createFulfillment(self, payload):
        fulfillmentData = self.requestAPI(
            method="POST", url=f"/fulfillments.json", payload=payload)

        return fulfillmentData
