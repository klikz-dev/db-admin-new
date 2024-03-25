from django.core.management.base import BaseCommand
from feed.models import OliviaQuinn

import os
import openpyxl

from utils import database, debug, common

BRAND = "Olivia & Quinn"
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
                feeds=OliviaQuinn.objects.all(), private=False)

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
            brand=BRAND, Feed=OliviaQuinn)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def fetchFeed(self):
        # Get Product Feed
        products = []

        wb = openpyxl.load_workbook(
            f"{FILEDIR}/oliviaquinn-master.xlsx", data_only=True)
        sh = wb.worksheets[0]

        for row in sh.iter_rows(min_row=3, values_only=True):
            try:
                # Primary Keys
                pattern = common.toText(row[3])
                color = common.toText(row[4])

                mpn = f"{common.toInt(row[2])}-{pattern.replace(' ', '-')}-{color.replace(' ', '-')}"
                sku = f"OQ {mpn}"

                # Categorization
                brand = BRAND
                manufacturer = BRAND
                type = common.toText(row[5]).title()
                collection = common.toText(row[1])

                # Main Information
                description = common.toText(row[19])
                width = common.toFloat(row[16])
                length = common.toFloat(row[15])
                height = common.toFloat(row[17])

                # Additional Information
                material = common.toText(row[12])
                country = common.toText(row[35])
                weight = common.toFloat(row[14])

                dimension = common.toText(row[18])
                specs = [
                    ("Dimension", dimension),
                ]

                # Pricing
                cost = common.toFloat(row[7])

                # Measurement
                uom = "Item"

                # Taggingf
                keywords = f"{material}, {description}"
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
                if boxWidth > 95 or boxHeight > 95 or boxDepth > 95 or boxWeight > 40:
                    whiteGlove = True
                else:
                    whiteGlove = False

                # Fine-tuning
                type = common.pluralToSingular(type)
                TYPE_DICT = {
                    "Swivel Chair": "Chair",
                    "Loveseat": "Chair",
                    "Executive Swivel Chair": "Chair",
                    "Swivel Ottoman": "Ottoman",
                    "Bench Ottoman": "Ottoman",
                    "Cube Ottoman": "Ottoman",
                }
                type = TYPE_DICT.get(type, type)

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
                'height': height,

                'material': material,
                'country': country,
                'weight': weight,

                'specs': specs,

                'uom': uom,

                'cost': cost,

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

        products = OliviaQuinn.objects.all()
        for product in products:
            stock = {
                'sku': product.sku,
                'quantity': 5,
                'note': ''
            }
            stocks.append(stock)

        return stocks
