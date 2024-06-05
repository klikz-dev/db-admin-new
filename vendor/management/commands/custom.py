from django.core.management.base import BaseCommand

import os
import glob
import environ
import openpyxl
import json

from utils import shopify, debug, common

from monitor.models import Log
from vendor.models import Product, Sync, Tag

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

        if "collections" in options['functions']:
            processor.collections()


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

    def collections(self):

        shopifyManager = shopify.ShopifyManager()

        ### Fix Buggy Collections ###
        shopifyCollections = shopifyManager.getCollections()
        for shopifyCollection in shopifyCollections:

            newRules = []

            for rule in shopifyCollection['rules']:
                newRule = {}

                if "Category:" in rule['condition']:

                    condition = rule['condition']
                    if condition == "Category:Dog":
                        condition = "Category:Animals>Dog"
                    if condition == "Category:Horse":
                        condition = "Category:Animals>Horse"
                    if condition == "Category:Leopard":
                        condition = "Category:Animals>Leopard"
                    if condition == "Category:Zebra":
                        condition = "Category:Animals>Zebra"
                    if condition == "Category:Fish":
                        condition = "Category:Animals>Fish"

                    newRule = {
                        'column': rule['column'],
                        'relation': rule['relation'],
                        'condition': condition,
                    }

                elif "Color:" in rule['condition']:

                    condition = rule['condition']
                    if condition == "Color:Black/White":
                        condition = "Color:Black and White"
                    if condition == "Color:Blue Green":
                        condition = "Color:Blue/Green"

                    newRule = {
                        'column': rule['column'],
                        'relation': rule['relation'],
                        'condition': condition,
                    }

                elif rule['column'] == "tag" and ":" not in rule['condition']:

                    condition = rule['condition']
                    if condition == "Best Selling":
                        condition = "Group:Best Selling"

                    newRule = {
                        'column': rule['column'],
                        'relation': rule['relation'],
                        'condition': condition,
                    }

                else:
                    newRule = rule

                if newRule not in newRules:
                    newRules.append(newRule)

            if newRules != shopifyCollection['rules']:
                shopifyManager.updateCollection(
                    collection=shopifyCollection, newRules=newRules)
                debug.log(
                    "Custom", f"Updated buggy collection {shopifyCollection['handle']}")
        ### Fix Buggy Collections ###

        return

        ### Report Existing Collections ###
        collectionReports = []

        def getCollection(index, collection):
            shopifyManager = shopify.ShopifyManager(thread=index)
            collectionData = shopifyManager.getCollection(
                collectionId=collection['id'])
            count = collectionData['products_count']

            if count < 10:
                shopifyManager.deleteCollection(collectionId=collection['id'])
                return

            collectionReport = (
                collection['id'], collection['handle'], collection['title'], count, str(collection['rules']))

            collectionReports.append(collectionReport)

            debug.log(
                "Custom", f"{index}/{len(shopifyCollections)} -- Collection {collection['id']}")

        common.thread(rows=shopifyCollections, function=getCollection)

        sorted_collectionReports = sorted(
            collectionReports, key=lambda x: x[3], reverse=False)

        common.writeDatasheet(
            filePath=f"{FILEDIR}/collections-report.xlsx",
            header=['ID', 'Handle', 'Title', 'Product Count', 'Rules'],
            rows=sorted_collectionReports
        )
        ### Report Existing Collections ###
