from django.core.management.base import BaseCommand
from feed.models import Maxwell

import os
import requests
import json
import re
import environ
import time

from utils import database, debug, common

env = environ.Env()

BRAND = "Maxwell"
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
            brand=BRAND, Feed=Maxwell)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def requestAPI(self, url):
        try:
            responseData = requests.get(
                f"{env('MAXWELL_API_URL')}/{url}",
                headers={'x-api-key': env('MAXWELL_API_KEY')}
            )
            responseJSON = json.loads(responseData.text)

            return responseJSON
        except Exception as e:
            debug.warn(BRAND, str(e))
            return None

    def testData(self):
        products = self.requestAPI("list?count=1000&page=1")
        print(products)

    def fetchFeed(self):
        # Get Product Feed
        products = []

        for page in range(1, 30):
            rows = self.requestAPI(f"list?count=1000&page={page}")
            debug.log(BRAND, f"{len(rows)} products from page {page}")

            for row in rows:
                try:
                    # Primary Keys
                    mpn = common.toText(row['sku'])
                    sku = f"MW {mpn}"

                    pattern = common.toText(row['style'])
                    color = common.toText(row['color']).replace("# ", "#")

                    # Categorization
                    brand = BRAND
                    manufacturer = BRAND

                    collection = common.toText(row['product_category'])

                    type = "Wallpaper" if "WALLPAPER" in collection else "Fabric"

                    # Main Information
                    description = common.toText(row['tests'])
                    width = common.toFloat(row['width'])

                    repeat = common.toText(row['repeat'])

                    # Additional Information
                    content = common.toText(row['content']).replace("\n", " ")

                    # Measurement
                    uom = "Roll" if type == "Wallpaper" else "Yard"

                    # Pricing
                    cost = common.toFloat(row['price'])

                    # Tagging
                    keywords = f"{collection} {pattern} {description}"
                    colors = color

                    # Image
                    thumbnail = common.toText(row['image_url'])

                    # Status
                    statusP = statusS = row['discontinued'] is None

                    # Fine-tuning
                    vPattern = r'V-(.*?)\"'
                    hPattern = r'H-(.*?)\"'

                    vPatternMatch = re.search(vPattern, repeat)
                    hPatternMatch = re.search(hPattern, repeat)

                    repeatV = common.toFloat(
                        vPatternMatch.group(1)) if vPatternMatch else 0
                    repeatH = common.toFloat(
                        hPatternMatch.group(1)) if hPatternMatch else 0

                    name = f"{pattern} {color} {type}"

                    # Exceptions
                    if mpn == "OPTIONS":
                        continue

                    if cost == 0 or not pattern or not color or not type:
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
                    'description': width,
                    'repeatV': repeatV,
                    'repeatH': repeatH,

                    'content': content,

                    'uom': uom,

                    'cost': cost,

                    'keywords': keywords,
                    'colors': colors,

                    'thumbnail': thumbnail,

                    'statusP': statusP,
                    'statusS': statusS,
                }
                products.append(product)

        return products

    def inventory(self):
        stocks = []

        products = Maxwell.objects.filter(statusP=True)
        for product in products:
            mpn = product.mpn
            sku = product.sku

            try:
                data = self.requestAPI(f"lookup?sku={mpn}")

                stockP = common.toInt(data["inventory"]["on_hand"])

                print(sku, stockP)

                stock = {
                    'sku': sku,
                    'quantity': stockP,
                    'note': ""
                }
                stocks.append(stock)

                time.sleep(0.5)

            except Exception as e:
                continue

        return stocks
