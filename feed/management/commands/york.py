from django.core.management.base import BaseCommand
from feed.models import York

import os
import requests
import json
import re
import environ

from utils import database, debug, common

env = environ.Env()

BRAND = "York"
FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "test" in options['functions']:
            processor = Processor()
            processor.testData()

        if "feed" in options['functions']:
            processor = Processor()
            feeds = processor.fetchFeed()
            processor.DatabaseManager.writeFeed(feeds=feeds)

        if "validate" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.validateFeed()

        if "status" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.statusSync(fullSync=False)

        if "content" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.contentSync()

        if "price" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.priceSync()

        if "tag" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.tagSync()

        if "add" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.addProducts()

        if "update" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.updateProducts(
                feeds=York.objects.all())

        if "image" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.downloadImages()

        if "inventory" in options['functions']:
            processor = Processor()
            stocks = processor.inventory()
            processor.DatabaseManager.updateInventory(
                stocks=stocks, type=1, reset=True)


class Processor:
    def __init__(self):
        self.DatabaseManager = database.DatabaseManager(
            brand=BRAND, Feed=York)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def requestAPI(self, url):
        try:
            responseData = requests.get(f"{env('YORK_API_URL')}/{url}")
            responseJSON = json.loads(responseData.text)
            result = responseJSON['results']

            return result
        except Exception as e:
            debug.warn(BRAND, str(e))
            return None

    def testData(self):
        product = self.requestAPI("product.php/VG4415")
        print(product[0])

    def fetchFeed(self):
        # Get Product Feed
        products = []

        collections = self.requestAPI("collections.php")

        for collection in collections:
            collectionID = collection['collectionID']
            collectionName = collection['name']

            if collectionID == "":
                continue

            debug.log(BRAND, f"Fetch Collection {collectionName}")

            productsData = self.requestAPI(f"collection.php/{collectionID}")

            for product in productsData:
                productID = product['productID']

                productData = self.requestAPI(f"product.php/{productID}")
                row = productData[0]

                try:
                    mpn = common.toText(row['VendorItem#'])
                    sku = f"YORK {mpn}"

                    pattern = common.toText(
                        re.sub(r'\s{2,}', ' ', re.sub(r'Wallpaper|\"', '', row['ProductName'])))
                    color = common.toText(
                        re.sub(r'\"', '', re.sub(r',\s*', '/', row['Color'])))

                    # Categorization
                    brand = BRAND
                    type = "Wallpaper"
                    manufacturer = common.toText(row['CategoryName'])
                    collectionName = common.toText(row['CollectionName'])

                    # Main Information
                    description_parts = [common.toText(row[key]) for key in [
                        'AdvertisingCopy', 'AdvertisingCopyII', 'AdvertisingCopyIII'] if row[key]]
                    description = ' '.join(description_parts).strip()

                    # Additional Information
                    match = common.toText(row['Match'])
                    usage = "Wallcovering"
                    country = common.toText(row['CountryOfOrigin'])
                    upc = common.toText(row['UPC'])

                    dimension = common.toText(row['ProductDimension'])
                    repeat = common.toText(row['PatternRepeat'])

                    specs = [
                        ("Dimension", dimension),
                        ("Repeat", repeat),
                    ]
                    features = [common.toText(row['KeyFeatures'])]

                    # Measurement
                    uom = common.toText(row['UOM']).title()
                    minimum = common.toInt(row['OrderIncrement'])
                    increment = minimum

                    # Pricing
                    cost = common.toFloat(row['DECBESTPRICE'])
                    msrp = common.toFloat(row['MSRP'])
                    map = common.toFloat(row['NewMap'])

                    # Tagging
                    keywords = f"{row['Substrate']} {row['Theme']} {pattern} {collection} {description}"
                    colors = color

                    # Status determination
                    statusP = row['SKUStatus'] in ("Active", "Retired")
                    statusS = row['SKUStatus'] in ("Active")
                    outlet = row['SKUStatus'] in ("Retired")
                    quickShip = row['QuickShip'] == 'Y'

                    # Fine-tuning
                    statusS = False
                    name = f"{pattern} {color} {type}"

                    # Exceptions
                    if cost == 0 or not pattern or not color or not type or not uom:
                        continue

                except Exception as e:
                    debug.warn(BRAND, str(e))
                    continue

            product = {
                'mpn': mpn,
                'sku': sku,
                'pattern': pattern,
                'color': color,
                'name': name,

                'brand': brand,
                'type': type,
                'manufacturer': manufacturer,
                'collection': collection,

                'description': description,

                'match': match,
                'usage': usage,
                'features': features,
                'specs': specs,
                'usage': usage,
                'country': country,
                'upc': upc,

                'uom': uom,
                'minimum': minimum,
                'increment': increment,

                'cost': cost,
                'msrp': msrp,
                'map': map,

                'keywords': keywords,
                'colors': colors,

                'statusP': statusP,
                'statusS': statusS,
                'outlet': outlet,
                'quickShip': quickShip,
            }
            products.append(product)

        return products

    def inventory(self):
        stocks = []

        products = York.objects.filter(statusP=True)
        for product in products:
            mpn = product.mpn
            sku = product.sku

            try:
                data = self.requestAPI(f"stock.php/{mpn}")

                stockP = common.toInt(data[0]["amount"])

                print(sku, stockP)

                stock = {
                    'sku': sku,
                    'quantity': stockP,
                    'note': ""
                }
                stocks.append(stock)
            except Exception as e:
                continue

        return stocks
