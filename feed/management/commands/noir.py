from django.core.management.base import BaseCommand
from feed.models import NOIR

import os
import openpyxl
import csv
import codecs

from utils import database, debug, common

BRAND = "NOIR"
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
                src="/noir/NOIR_MASTER.xlsx",
                dst=f"{FILEDIR}/noir-master.xlsx",
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
            processor.DatabaseManager.statusSync(fullSync=True)

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
                feeds=NOIR.objects.all(), private=False)

        if "image" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.downloadImages()

        if "inventory" in options['functions']:
            common.downloadFileFromSFTP(
                brand=BRAND,
                src="/noir/inventory/NOIR_INV.csv",
                dst=f"{FILEDIR}/noir-inventory.csv",
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
            brand=BRAND, Feed=NOIR)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def fetchFeed(self):
        # Get Product Feed
        products = []

        wb = openpyxl.load_workbook(
            f"{FILEDIR}/noir-master.xlsx", data_only=True)
        sh = wb.worksheets[0]

        for row in sh.iter_rows(min_row=2, values_only=True):
            # try:
            if True:
                # Primary Keys
                mpn = common.toText(row[2])
                sku = f"NOIR {mpn}"

                pattern = common.toText(row[6])
                color = common.toText(row[20])

                name = common.toText(row[6])

                # Categorization
                brand = BRAND
                manufacturer = BRAND
                type = common.toText(row[5]).title()
                collection = f"{brand} {type}"

                # Main Information
                description = common.toText(row[19])
                width = common.toFloat(row[16])
                length = common.toFloat(row[15])
                height = common.toFloat(row[17])

                # Additional Information
                material = common.toText(row[12])
                country = common.toText(row[35])
                weight = common.toFloat(row[14])
                upc = common.toInt(row[13])

                dimension = common.toText(row[18])
                specs = [
                    ("Dimension", dimension),
                ]

                # Pricing
                cost = common.toFloat(row[7])
                map = common.toFloat(row[8])

                # Measurement
                uom = "Item"

                # Tagging
                keywords = f"{color}, {material}, {description}, {name}"
                colors = color

                # Image
                thumbnail = row[51].replace("dl=0", "dl=1")
                roomsets = [row[id].replace("dl=0", "dl=1")
                            for id in range(52, 65) if row[id]]

                # Status
                statusP = True
                statusS = False

                # Shipping
                boxHeight = common.toFloat(row[43])
                boxWidth = common.toFloat(row[44])
                boxDepth = common.toFloat(row[45])
                boxWeight = common.toFloat(row[42])
                if boxWidth > 95 or boxHeight > 95 or boxDepth > 95 or boxWeight > 40 or weight > 40:
                    whiteGlove = True
                else:
                    whiteGlove = False

                # Fine-tuning
                type = common.pluralToSingular(type)
                TYPE_DICT = {
                    "Occasional Chair": "Chair",
                    "Ocassional Chair": "Chair",
                    "Desks, Accent Table": "Accent Table",
                    "Stools, Accent Table": "Accent Table",
                    "Cocktail Tables, Accent Table": "Accent Table",
                    "Bar & Counter": "Bar Stool",
                    "Sideboard": "Side Table",
                    "Console/Accent Table": "Accent Table",
                    "Sconce": "Wall Sconce",
                }
                type = TYPE_DICT.get(type, type)

                if "," in pattern:
                    pattern, color = [item.strip()
                                      for item in name.split(",", 1)]

                name = name.replace(",", "")

                # Exceptions
                if cost == 0 or not pattern or not color or not type:
                    continue

            # except Exception as e:
            #     debug.warn(BRAND, str(e))
            #     continue

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

                'material': material,
                'country': country,
                'weight': weight,
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

                'whiteGlove': whiteGlove,
            }
            products.append(product)

        return products

    def inventory(self):
        stocks = []

        f = open(f"{FILEDIR}/noir-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
        for row in cr:
            mpn = common.toText(row[0])

            try:
                product = NOIR.objects.get(mpn=mpn)
            except NOIR.DoesNotExist:
                continue

            sku = product.sku
            stockP = common.toInt(row[2])

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': ""
            }
            stocks.append(stock)

        return stocks
