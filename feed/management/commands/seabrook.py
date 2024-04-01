from django.core.management.base import BaseCommand
from feed.models import Seabrook

import os
import environ
import openpyxl
import requests
import json

from utils import database, debug, common

env = environ.Env()

BRAND = "Seabrook"
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

        if "update" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.updateProducts(
                feeds=Seabrook.objects.all())

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
            brand=BRAND, Feed=Seabrook)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def requestAPI(self, mpn):
        responseData = requests.get(
            f"https://stock.wallcovering.info/v1/api/item/{mpn}",
            headers={
                'x-api-key': env('SEABROOK_KEY')
            }
        )
        responseJson = json.loads(responseData.text)

        return responseJson

    def fetchFeed(self):
        # Get Product Feed
        products = []

        wb = openpyxl.load_workbook(
            f"{FILEDIR}/seabrook-master.xlsx", data_only=True)
        sh = wb.worksheets[0]

        for row in sh.iter_rows(min_row=3, values_only=True):
            try:
                # Primary Keys
                mpn = common.toText(row[3])
                sku = f"SB {mpn}"

                pattern = common.toText(row[5])
                color = common.toText(row[9])

                # Categorization
                brand = BRAND
                manufacturer = BRAND

                type = common.toText(row[18]).title()
                collection = common.toText(row[2])

                # Main Information
                description = common.toText(row[6])
                width = common.toFloat(row[29])
                length = common.toFloat(row[30])
                repeatH = common.toFloat(row[34])

                # Additional Information
                yardsPR = common.toFloat(row[22])
                usage = type
                finish = common.toText(row[11])
                material = common.toText(row[40])
                care = common.toText(row[38])
                weight = common.toFloat(row[21])
                country = common.toText(row[42])
                upc = common.toInt(row[16])

                coverage = f"{common.toText(row[32])} sqft"
                removal = common.toText(row[39])
                specs = [
                    ("Coverage", coverage),
                    ("Removal", removal)
                ]

                # Measurement
                uom = common.toText(row[43])

                # Pricing
                cost_index, map_index = (
                    13, 15) if 'Bolt' in row[43] else (12, 14)

                cost = common.toFloat(row[cost_index])
                map = 0 if row[53] == "No" else common.toFloat(row[map_index])

                # Tagging
                keywords = f"{collection} {pattern} {description} {row[7]} {row[8]}"
                colors = common.toText(row[9])

                # Image
                thumbnail = row[45]
                roomsets = [row[46]]

                # Status
                statusP = collection not in [
                    'Lillian August Grasscloth Binder', 'Indigo', 'New Hampton']

                statusS = common.toText(row[17]) == "Y" and "JP3" not in mpn

                # Fine-tuning
                TYPE_DICT = {
                    "Border": "Wallpaper",
                    "Sidewall": "Wallpaper",
                    "Residential Use": "Wallpaper"
                }
                type = TYPE_DICT.get(type, type)

                UOM_DICT = {
                    "1 Bolt": "Double Roll",
                    "1 S/R": "Roll",
                    "1 Roll": "Roll",
                    "1 Yd": "Yard",
                    "1 Mural": "Meter",
                    "1 Meter": "Meter",
                }
                uom = UOM_DICT.get(uom, uom)

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
                'width': width,
                'length': length,
                'repeatH': repeatH,

                'yardsPR': yardsPR,
                'usage': usage,
                'finish': finish,
                'material': material,
                'care': care,
                'weight': weight,
                'country': country,
                'upc': upc,

                'specs': specs,

                'uom': uom,

                'cost': cost,
                'map': map,

                'keywords': keywords,
                'colors': colors,

                'thumbnail': thumbnail,
                'roomsets': roomsets,

                'statusP': statusP,
                'statusS': statusS,
            }
            products.append(product)

        return products

    def inventory(self):
        stocks = []

        products = Seabrook.objects.filter(statusP=True)
        for product in products:
            mpn = product.mpn
            sku = product.sku

            try:
                data = self.requestAPI(mpn)

                stockP = common.toInt(data["stock"]["units"])

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
