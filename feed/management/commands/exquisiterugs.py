from django.core.management.base import BaseCommand
from feed.models import ExquisiteRugs

import os
import openpyxl
import csv
import codecs

from utils import database, debug, common

BRAND = "Exquisite Rugs"
FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "feed" in options['functions']:
            processor = Processor()
            common.downloadFileFromSFTP(
                brand=BRAND,
                src="/exquisiterugs/datasheets/exquisiterugs-master.xlsx",
                dst=f"{FILEDIR}/exquisiterugs-master.xlsx",
                fileSrc=True,
                delete=False
            )
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
            common.downloadFileFromSFTP(
                brand=BRAND,
                src="/exquisiterugs/decoratorsbestam.csv",
                dst=f"{FILEDIR}/exquisiterugs-inventory.csv",
                fileSrc=True,
                delete=False
            )

            processor = Processor()
            stocks = processor.inventory()
            processor.DatabaseManager.updateInventory(
                stocks=stocks, type=1, reset=True)


class Processor:
    def __init__(self):
        self.DatabaseManager = database.DatabaseManager(
            brand=BRAND, Feed=ExquisiteRugs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def fetchFeed(self):
        # Get Product Feed
        products = []

        wb = openpyxl.load_workbook(
            f"{FILEDIR}/exquisiterugs-master.xlsx", data_only=True)
        sh = wb.worksheets[0]

        for row in sh.iter_rows(min_row=2, values_only=True):
            try:
                # Primary Keys
                mpn = common.toText(row[2]).replace("'", "")
                sku = f"ER {mpn}"

                pattern = common.toInt(row[3])
                color = common.toText(row[4])

                name = common.toText(row[6])

                # Categorization
                brand = BRAND
                type = "Rug"
                manufacturer = BRAND
                collection = common.toText(row[1])

                # Main Information
                description = common.toText(row[19])

                width = common.toFloat(row[15])
                length = common.toFloat(row[16])
                height = common.toFloat(row[17])

                size = f"{common.toFloat(width / 12)}' x {common.toFloat(length / 12)}'"

                # Additional Information
                material = common.toText(row[12])
                care = common.toText(row[25])
                disclaimer = common.toText(row[24])
                country = common.toText(row[35])
                upc = common.toInt(row[13])
                weight = common.toFloat(row[14])

                specs = [
                    ("Dimension", common.toText(row[18])),
                ]

                # Measurement
                uom = "Item"

                # Pricing
                cost = common.toFloat(row[7])
                map = common.toFloat(row[8])

                # Tagging
                keywords = f"{collection} {pattern} {description} {row[11]} {material}"
                colors = color

                # Image
                thumbnail = common.toText(row[51])

                roomsets = []
                for id in range(52, 58):
                    if row[id]:
                        roomsets.append(row[id])

                # Status
                statusP = True
                statusS = False

                # Shipping
                shippingWidth = common.toFloat(row[44])
                shippingLength = common.toFloat(row[43])
                shippingHeight = common.toFloat(row[45])
                shippingWeight = common.toFloat(row[42])

                if shippingWidth > 95 or shippingLength > 95 or shippingHeight > 95 or shippingWeight > 40:
                    whiteGlove = True
                else:
                    whiteGlove = False

                # Fine-tuning
                name = f"{name.replace('Area Rug', '')}{size} Area Rug".replace(
                    color, f"{pattern} {color}")

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
                'height': height,
                'size': size,

                'material': material,
                'care': care,
                'country': country,
                'weight': weight,
                'upc': upc,
                'disclaimer': disclaimer,

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
                'whiteGlove': whiteGlove,
            }
            products.append(product)

        return products

    def inventory(self):
        stocks = []

        f = open(f"{FILEDIR}/exquisiterugs-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
        for row in cr:
            mpn = common.toText(row[1]).replace("'", "")

            try:
                product = ExquisiteRugs.objects.get(mpn=mpn)
            except ExquisiteRugs.DoesNotExist:
                continue

            sku = product.sku
            stockP = common.toInt(row[2])
            stockNote = common.toInt(row[3])

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': stockNote
            }
            stocks.append(stock)

        return stocks
