from django.core.management.base import BaseCommand
from feed.models import Kasmir

import os
import environ
import xlrd

from utils import database, debug, common

env = environ.Env()

BRAND = "Kasmir"
FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "feed" in options['functions']:
            common.downloadFileFromFTP(
                brand=BRAND,
                src="Current-Inventory_Int.xls",
                dst=f"{FILEDIR}/kasmir-master.xls"
            )

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
                feeds=Kasmir.objects.all())

        if "image" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.downloadImages()

        if "inventory" in options['functions']:
            common.downloadFileFromFTP(
                brand=BRAND,
                src="Current-Inventory_Int.xls",
                dst=f"{FILEDIR}/kasmir-master.xls"
            )

            processor = Processor()
            stocks = processor.inventory()
            processor.DatabaseManager.updateInventory(
                stocks=stocks, type=1, reset=True)


class Processor:
    def __init__(self):
        self.DatabaseManager = database.DatabaseManager(
            brand=BRAND, Feed=Kasmir)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def fetchFeed(self):
        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/kasmir-master.xls")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            row = sh.row_values(i)

            try:
                # Primary Keys
                pattern = common.toText(row[0])
                color = common.toText(row[1])

                mpn = f"{pattern}/{color}"
                sku = f"KM {mpn}"

                # Categorization
                brand = BRAND
                manufacturer = BRAND
                type = "Fabric"
                collection = common.toInt(row[25])

                # Main Information
                width = common.toFloat(row[3])
                repeatV = common.toFloat(row[5])
                repeatH = common.toFloat(row[6])

                # Additional Information
                usage = common.toText(row[56])
                content = common.toText(row[26])

                specs = [
                    "Construction", common.toText(row[55])
                ]

                # Measurement
                uom = "Yard"

                # Pricing
                cost = common.toFloat(row[2]) / 2

                # Tagging
                keywords = f"{collection} {pattern} {row[54]}, {row[55]}"
                colors = color

                # Images
                thumbnail = f"https://www.kasmirfabricsonline.com/sampleimages/Large/{common.toText(row[57])}"

                # Status
                statusP = True
                statusS = True

                if "TEST" in pattern or cost < 8:
                    statusP = False

                if row[57] == "ImageComingSoon.jpg":
                    thumbnail = ""

                name = f"{pattern} {color} {type}".title()

                # Exceptions
                if "BOOKPATTERN" == pattern.upper() or "ALCANTARA" in pattern.upper():
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

                'width': width,
                'repeatV': repeatV,
                'repeatH': repeatH,

                'content': content,
                'usage': usage,

                'specs': specs,

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

        wb = xlrd.open_workbook(f"{FILEDIR}/kasmir-master.xls")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            row = sh.row_values(i)

            pattern = common.toText(row[0])
            color = common.toText(row[1])

            mpn = f"{pattern}/{color}"

            try:
                product = Kasmir.objects.get(mpn=mpn)
            except Kasmir.DoesNotExist:
                continue

            sku = product.sku
            stockP = common.toInt(sh.cell_value(i, 58))

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': ""
            }
            stocks.append(stock)

        return stocks
