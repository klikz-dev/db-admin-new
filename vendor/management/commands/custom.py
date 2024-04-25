from django.core.management.base import BaseCommand

import os
import glob
import requests
import environ

from utils import shopify, common

from vendor.models import Product, Sync
from monitor.models import Log

env = environ.Env()

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"


class Command(BaseCommand):
    help = f"Migrate Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()

        if "clean" in options['functions']:
            processor.clean()

        if "delete" in options['functions']:
            processor.delete()


class Processor:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def clean(self):
        # Empty Image folders
        imageFolders = ["thumbnail", "roomset", "hires", "compressed"]
        for imageFolder in imageFolders:
            for file in glob.glob(f"{FILEDIR}/images/{imageFolder}/*.*"):
                os.remove(file)

        # Empty Logs
        Log.objects.all().delete()

        # Empty Syncs
        Sync.objects.all().delete()

    def delete(self):

        shopifyManager = shopify.ShopifyManager()

        def deleteProduct(_, product_id):
            print(f"Delete: {product_id}")
            shopifyManager.deleteProduct(product_id)

        base_url = f"https://decoratorsbest.myshopify.com/admin/api/2024-01/products.json"
        params = {'limit': 250, 'fields': 'id,published_at'}
        headers = {"X-Shopify-Access-Token": env('SHOPIFY_API_TOKEN')}

        session = requests.Session()
        session.headers.update(headers)

        response = session.get(base_url, params=params)

        page = 1
        while True:
            print(f"Reviewing Products {250 * (page - 1) + 1} - {250 * page}")

            products = response.json()['products']
            product_ids = {str(product['id']) for product in products}

            existing_product_ids = set(Product.objects.filter(
                shopifyId__in=product_ids).values_list('shopifyId', flat=True).distinct())

            products_to_remove = product_ids - existing_product_ids

            common.thread(rows=products_to_remove, function=deleteProduct)

            if 'next' in response.links:
                next_url = response.links['next']['url']
                response = session.get(next_url)
                page += 1
            else:
                break
