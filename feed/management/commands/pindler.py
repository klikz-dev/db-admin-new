from django.core.management.base import BaseCommand
from feed.models import Pindler

import os
import environ
import requests
import json
import csv
import codecs

from utils import database, debug, common

env = environ.Env()

BRAND = "Pindler"
FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "feed" in options['functions']:
            processor = Processor()
            processor.downloadFeed()
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
                feeds=Pindler.objects.all())

        if "image" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.downloadImages()

        if "inventory" in options['functions']:
            processor = Processor()
            stocks = processor.inventory()
            processor.DatabaseManager.updateInventory(
                stocks=stocks, type=3, reset=True)


class Processor:
    def __init__(self):
        self.DatabaseManager = database.DatabaseManager(
            brand=BRAND, Feed=Pindler)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def downloadFeed(self):
        try:
            r = requests.get(
                "https://trade.pindler.com/dataexport/DecoratorBest/DECORBEST.csv",
                auth=(env('PINDLER_UN'), env('PINDLER_PW'))
            )

            with open(f"{FILEDIR}/pindler-master.csv", "wb") as out:
                for bits in r.iter_content():
                    out.write(bits)

            debug.log(BRAND, "Downloaded Pindler FTP Master CSV")

        except Exception as e:
            debug.warn(BRAND, str(e))

    def fetchFeed(self):
        # Get Product Feed
        products = []

        f = open(f"{FILEDIR}/pindler-master.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, 'utf-8'))

        for row in cr:
            try:
                if row[0] == "Inventory Number" or row[0] == "Text":
                    continue

                # Primary Keys
                mpn = row[0]
                sku = f"PDL {row[20]}-{row[18]}".replace("'", "")

                pattern = common.toText(row[19])
                color = common.toText(row[18])

                # Categorization
                brand = BRAND
                manufacturer = BRAND

                type = "Trim" if "T" in row[20] else "Fabric"

                collection = row[1] or row[3]

                # Main Information
                width = common.toText(row[26])
                repeatV = common.toFloat(row[24])
                repeatH = common.toFloat(row[9])

                # Additional Information
                content = common.toText(row[4])

                # Measurement
                uom = "Yard"

                # Pricing
                cost = common.toFloat(row[25])

                # Tagging
                keywords = " ".join(
                    [row[12], row[13], row[14], row[15], row[16], row[17]])
                colors = row[12]

                # Image
                thumbnail = common.toText(row[10])

                # Status
                statusP = True
                statusS = False

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

                'width': width,
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

        f = open(f"{FILEDIR}/pindler-master.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, 'utf-8'))

        for row in cr:
            try:
                if row[0] == "Inventory Number" or row[0] == "Text":
                    continue

                sku = f"PDL {row[20]}-{row[18]}".replace("'", "")

                stockP = row[11]

                if stockP == "IN STOCK":
                    stockP = 10
                else:
                    stockP = common.toInt(stockP)

                stock = {
                    'sku': sku,
                    'quantity': stockP,
                    'note': ""
                }
                stocks.append(stock)
            except Exception as e:
                continue

        return stocks
