from django.core.management.base import BaseCommand

import os
import glob
import environ

from utils import shopify, debug, common

from monitor.models import Log
from vendor.models import Product, Sync

env = environ.Env()

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"


class Command(BaseCommand):
    help = f"Migrate Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()

        if "cleanup-images" in options['functions']:
            processor.cleanupImages()

        if "cleanup-logs" in options['functions']:
            processor.cleanupLogs()

        if "disable-brand" in options['functions']:
            processor.disableBrand()

        if "delete-brand" in options['functions']:
            processor.deleteBrand()

        if "refresh" in options['functions']:
            processor.refresh()

        if "report" in options['functions']:
            processor.report()


class Processor:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def cleanupImages(self):
        # Empty Image folders
        imageFolders = ["thumbnail", "roomset", "hires", "compressed"]
        for imageFolder in imageFolders:
            for file in glob.glob(f"{FILEDIR}/images/{imageFolder}/*.*"):
                os.remove(file)

    def cleanupLogs(self):
        # Empty Logs
        Log.objects.all().delete()

    def disableBrand(self):
        brand = "Phillip Jeffries"

        products = Product.objects.filter(manufacturer__brand=brand)

        for product in products:
            if product.published:
                product.published = False
                product.save()

                Sync.objects.get_or_create(
                    productId=product.shopifyId, type="Status")

    def deleteBrand(self):
        brand = "Poppy"

        shopifyManager = shopify.ShopifyManager()

        products = Product.objects.filter(manufacturer__brand=brand)

        for product in products:
            shopifyManager.deleteProduct(productId=product.shopifyId)
            product.delete()

    def refresh(self):
        products = Product.objects.all()

        total = len(products)

        def syncContent(index, product):

            shopifyManager = shopify.ShopifyManager(
                product=product, thread=index)

            handle = shopifyManager.updateProduct()

            if handle:
                product.shopifyHandle = handle
                product.save()

            debug.log(
                "Custom", f"{index}/{total}: Content Sync for {product.shopifyId} has been completed.")

        common.thread(rows=products, function=syncContent)

    def report(self):
        collectionReports = []

        shopifyManager = shopify.ShopifyManager()
        collections = shopifyManager.getCollections()
        for collection in collections:
            type = "smart" if "rules" in collection else "custom"
            collectionData = shopifyManager.getCollection(
                type=type, collectionId=collection['id'])
            count = collectionData['products_count']

            collectionReport = (
                collection['id'], collection['handle'], collection['title'], count)

            print(collectionReport)
            collectionReports.append(collectionReport)

        sorted_collectionReports = sorted(
            collectionReports, key=lambda x: x[3], reverse=False)

        common.writeDatasheet(
            filePath=f"{FILEDIR}/collections-report.xlsx",
            header=['ID', 'Handle', 'Title', 'Product Count'],
            rows=sorted_collectionReports
        )
