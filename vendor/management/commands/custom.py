from concurrent.futures import ThreadPoolExecutor
import requests
import json
import environ
import os
from django.db import transaction

from django.core.management.base import BaseCommand

from utils import debug, shopify
from vendor.models import Product, Image, Sync


env = environ.Env()

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"


class Command(BaseCommand):
    help = f"Migrate Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()

        if "image" in options['functions']:
            processor.image()

        if "cleanup" in options['functions']:
            processor.cleanup()

        if "collections" in options['functions']:
            processor.collections()

        if "sync-status" in options['functions']:
            processor.syncStatus()

        if "sync-price" in options['functions']:
            processor.syncPrice()

        if "sync-tag" in options['functions']:
            processor.syncTag()

        if "sync-content" in options['functions']:
            processor.syncContent()


class Processor:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def requestAPI(self, url):
        responseData = requests.get(
            url,
            headers={
                'Authorization': 'Token d71bcdc1b60d358e01182da499fd16664a27877a'
            }
        )
        responseJson = json.loads(responseData.text)

        return responseJson

    def image(self):
        Image.objects.filter(product__manufacturer__brand="York").delete()

        products = Product.objects.filter(manufacturer__brand="York")
        total = len(products)

        def importImage(index, product):
            imagesData = self.requestAPI(
                f"https://www.decoratorsbestam.com/api/images/?product={product.shopifyId}")

            imagesArray = imagesData['results']

            for image in imagesArray:
                imageURL = image['imageURL']
                imageIndex = image['imageIndex']

                if imageIndex == 20:
                    continue

                Image.objects.update_or_create(
                    url=imageURL,
                    position=imageIndex,
                    product=product,
                    hires=False,
                )

                debug.log(
                    "Migrator", f"{index}/{total} - {product} image {imageURL}")

        with ThreadPoolExecutor(max_workers=100) as executor:
            for index, product in enumerate(products):
                executor.submit(importImage, index, product)

    def cleanup(self):

        # Temp: Enable JFF Casadeco, Caselio, ILIV
        shopifyManager = shopify.ShopifyManager()

        vendors = ["Casadeco", "Caselio", "ILIV"]
        for vendor_name in vendors:
            base_url = f"https://decoratorsbest.myshopify.com/admin/api/2024-01/products.json"
            params = {'vendor': vendor_name,
                      'limit': 250, 'fields': 'id,title'}
            headers = {"X-Shopify-Access-Token": env('SHOPIFY_API_TOKEN')}

            session = requests.Session()
            session.headers.update(headers)

            response = session.get(base_url, params=params)

            page = 1
            while True:
                print(
                    f"Reviewing Products {250 * (page - 1) + 1} - {250 * page}")

                products = response.json()['products']

                product_ids = {
                    str(product['id']) for product in products}

                existing_product_ids = set(Product.objects.filter(
                    shopifyId__in=product_ids).values_list('shopifyId', flat=True).distinct())

                products_to_remove = product_ids - existing_product_ids

                for product_id in products_to_remove:
                    print(f"Publish: {product_id}")

                    shopifyManager.updateProductStatus(
                        productId=product_id, status=True)

                    shopifyManager.requestAPI(
                        method="PUT",
                        url=f"/products/{product_id}.json",
                        payload={
                            "product":
                            {
                                'id': product_id,
                                "tags": "Group:No Sample",
                            }
                        }
                    )

                if 'next' in response.links:
                    next_url = response.links['next']['url']
                    response = session.get(next_url)
                    page += 1
                else:
                    break

        return

    def collections(self):

        base_url = f"https://decoratorsbest.myshopify.com/admin/api/2024-01/smart_collections.json"
        params = {'limit': 250, 'fields': 'id,handle,rules'}
        headers = {"X-Shopify-Access-Token": env('SHOPIFY_API_TOKEN')}

        session = requests.Session()
        session.headers.update(headers)

        response = session.get(base_url, params=params)

        # Get Collections
        collections = []
        while True:
            collections = response.json()['smart_collections']

            for collection in collections:
                print(f"Updating: {collection['handle']}")

                collections.append({
                    'id': collection['id'],
                    'handle': collection['handle'],
                    'rules': collection['rules']
                })

            if 'next' in response.links:
                next_url = response.links['next']['url']
                response = session.get(next_url)
            else:
                break

        with open(f"{FILEDIR}/collections.json", 'w') as outfile:
            json.dump(collections, outfile, indent=2)

        # Fix Collection Rules
        for i, collection in enumerate(collections):
            rules = collection['rules']
            for index, rule in enumerate(rules):
                if rule['column'] == "type" and "Throw Pillows" == rule['condition']:
                    rules[index]['condition'] = "Pillow"

            collections[i]['rules'] = rules

        # Push Updated Collection Rules
        for collection in collections:
            try:
                requests.request(
                    "PUT",
                    f"https://decoratorsbest.myshopify.com/admin/api/2024-01/smart_collections/{collection['id']}.json",
                    headers=headers,
                    json={
                        "smart_collection": {
                            "rules": collection['rules']
                        }
                    }
                )

                print(collection['handle'])
            except Exception as e:
                print(e)
                continue

    def syncStatus(self):

        Sync.objects.filter(type="Status").delete()

        product_ids = Product.objects.values_list('shopifyId', flat=True)

        sync_objects = [Sync(productId=shopify_id, type="Status")
                        for shopify_id in product_ids]

        with transaction.atomic():
            try:
                Sync.objects.bulk_create(sync_objects)
            except Exception as e:
                print(e)

    def syncPrice(self):

        Sync.objects.filter(type="Price").delete()

        product_ids = Product.objects.values_list('shopifyId', flat=True)

        sync_objects = [Sync(productId=shopify_id, type="Price")
                        for shopify_id in product_ids]

        with transaction.atomic():
            try:
                Sync.objects.bulk_create(sync_objects)
            except Exception as e:
                print(e)

    def syncTag(self):

        Sync.objects.filter(type="Tag").delete()

        product_ids = Product.objects.values_list('shopifyId', flat=True)

        sync_objects = [Sync(productId=shopify_id, type="Tag")
                        for shopify_id in product_ids]

        with transaction.atomic():
            try:
                Sync.objects.bulk_create(sync_objects)
            except Exception as e:
                print(e)

    def syncContent(self):

        Sync.objects.filter(type="Content").delete()

        product_ids = Product.objects.values_list('shopifyId', flat=True)

        sync_objects = [Sync(productId=shopify_id, type="Content")
                        for shopify_id in product_ids]

        with transaction.atomic():
            try:
                Sync.objects.bulk_create(sync_objects)
            except Exception as e:
                print(e)
