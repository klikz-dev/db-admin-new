from django.core.management.base import BaseCommand
from feed.models import PhillipJeffries

import os
import environ
import openpyxl
import requests
import json
import time

from utils import database, debug, common

env = environ.Env()

BRAND = "Phillip Jeffries"
FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
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
            brand=BRAND, Feed=PhillipJeffries)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def requestAPI(self, mpn):
        responseData = requests.get(
            f"https://www.phillipjeffries.com/api/products/skews/{mpn}.json")
        responseJson = json.loads(responseData.text)

        return responseJson

    def fetchFeed(self):
        # Get Product Feed
        products = []

        wb = openpyxl.load_workbook(
            f"{FILEDIR}/phillipjeffries-master.xlsx", data_only=True)
        sh = wb.worksheets[0]

        for row in sh.iter_rows(min_row=2, values_only=True):
            try:

                mpn = common.toInt(row[0])

                if mpn == 0:
                    continue
                if mpn < 100:
                    mpn = f"0{mpn}"

                debug.log(BRAND, f"Fetch Product MPN: {mpn}")
                data = self.requestAPI(mpn)

                # Primary Keys
                sku = 'PJ {}'.format(mpn)

                pattern = common.toText(data['collection']['name'])
                color = common.toText(data['specs']['color'])

                # Categorization
                brand = BRAND
                manufacturer = BRAND

                type = "Wallpaper"

                collection = ""
                for binder in data['collection']['binders']:
                    if binder['name']:
                        collection = common.toText(binder['name'])
                        break

                # Main Information
                description = common.toText(data['collection']['description'])

                # Additional Information
                specs = []
                for key, value in data['specs'].items():
                    if value:
                        specs.append((key.replace("_", " ").title(), value))

                # Measurement
                uom = "Yard"
                minimum = common.toInt(
                    data['order']['wallcovering']['minimum_order'])
                increment = common.toInt(
                    data['order']['wallcovering']['order_increment'])

                # Pricing
                cost = common.toFloat(
                    data['order']['wallcovering']['price']['amount'])

                # Tagging
                keywords = f"{collection} {description} {pattern}"
                colors = color

                # Assets
                thumbnail = f"https://www.phillipjeffries.com{data['assets']['download_src']}"

                # Status
                statusP = True
                statusS = False

                if data['order']['wallcovering']['purcode'] == "NJSTOCKED":
                    quickShip = True
                else:
                    quickShip = False

                # Fine-tuning
                name = f"{pattern} {color} {type}"

                # Exceptions
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

                'specs': specs,

                'uom': uom,
                'minimum': minimum,
                'increment': increment,

                'cost': cost,

                'keywords': keywords,
                'colors': colors,

                'thumbnail': thumbnail,

                'statusP': statusP,
                'statusS': statusS,

                'quickShip': quickShip,
            }
            products.append(product)

        return products

    def inventory(self):
        stocks = []

        products = PhillipJeffries.objects.filter(statusP=True)
        for product in products:
            mpn = product.mpn
            sku = product.sku

            try:
                data = self.requestAPI(mpn)

                stockP = 0
                for lot in data["stock"]["sales"]["lots"]:
                    stockP += common.toInt(lot["avail"])

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
