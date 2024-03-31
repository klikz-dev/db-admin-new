from django.core.management.base import BaseCommand
from feed.models import Covington

import os
import openpyxl
import csv
import codecs

from utils import database, debug, common

BRAND = "Covington"
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
            processor.DatabaseManager.contentSync(private=True)

        if "price" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.priceSync()

        if "tag" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.tagSync()

        if "add" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.addProducts(private=True)

        if "update" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.updateProducts(
                feeds=Covington.objects.all(), private=True)

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
            brand=BRAND, Feed=Covington)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def fetchFeed(self):
        # Get Product Feed
        products = []

        wb = openpyxl.load_workbook(
            f"{FILEDIR}/covington-master.xlsx", data_only=True)
        sh = wb.worksheets[0]

        for row in sh.iter_rows(min_row=2, values_only=True):
            try:
                # Primary Keys
                mpn = common.toText(row[0])
                sku = f"DBC {mpn}"
                pattern = common.toText(row[4])
                color = common.toText(row[5])

                # Categorization
                brand = BRAND
                manufacturer = BRAND
                type = "Fabric"
                collection = common.toText(row[2])

                # Main Information
                description = common.toText(row[9])
                width = common.toFloat(row[10])
                repeatH = common.toFloat(row[14])
                repeatV = common.toFloat(row[15])

                # Additional Information
                usage = common.toText(row[21])
                content = common.toText(row[13])
                upc = common.toInt(row[12])

                features = [common.toText(row[id])
                            for id in range(16, 19) if common.toText(row[id])]

                # Pricing
                cost = common.toFloat(row[6])

                # Measurement
                uom = "Yard"
                minimum = common.toInt(row[22])

                # Tagging
                keywords = f"{collection} {pattern} {description} {row[24]} {' '.join(features)}"
                colors = common.toText(row[25])

                # Status
                statusP = True
                statusS = True

                # Fine-tuning
                name = f"{pattern} {color} {type}"

                # Exceptions
                if "MG-" not in mpn:
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
                'width': width,
                'repeatV': repeatV,
                'repeatH': repeatH,

                'usage': usage,
                'content': content,
                'upc': upc,

                'features': features,

                'uom': uom,
                'minimum': minimum,

                'cost': cost,

                'keywords': keywords,
                'colors': colors,

                'statusP': statusP,
                'statusS': statusS,
            }
            products.append(product)

        return products

    def inventory(self):
        stocks = []

        f = open(f"{FILEDIR}/covington-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
        for row in cr:
            mpn = row[0]

            try:
                product = Covington.objects.get(mpn=mpn)
            except Covington.DoesNotExist:
                continue

            sku = product.sku
            stockP = common.toInt(row[5])

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': ""
            }
            stocks.append(stock)

        return stocks
