from django.core.management.base import BaseCommand
from feed.models import Zoffany

import os
import environ
import openpyxl

from utils import database, debug, common

env = environ.Env()

BRAND = "Zoffany"
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
                feeds=Zoffany.objects.all())

        if "image" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.downloadImages()


class Processor:
    def __init__(self):
        self.DatabaseManager = database.DatabaseManager(
            brand=BRAND, Feed=Zoffany)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def fetchFeed(self):
        # Get Product Feed
        products = []

        wb = openpyxl.load_workbook(
            f"{FILEDIR}/zoffany-master.xlsx", data_only=True)
        sh = wb.worksheets[0]

        for row in sh.iter_rows(min_row=2, values_only=True):
            try:
                # Primary Keys
                mpn = common.toText(row[2])
                sku = f"ZOF {mpn}"

                pattern = common.toText(row[7])
                color = common.toText(row[8])

                # Categorization
                brand = BRAND
                manufacturer = common.toText(row[21]).title()
                type = str(row[12])
                collection = common.toText(row[9])

                # Main Information
                description = common.toText(row[25])
                width = common.toFloat(row[18])
                repeatH = common.toFloat(row[20])
                repeatV = common.toFloat(row[19])

                # Additional Information
                yardsPR = common.toFloat(row[17])
                match = common.toText(row[14])
                usage = common.toText(row[13])

                features = [
                    f"Reversible: {common.toText(row[15])}"
                ]

                # Pricing
                cost = common.toFloat(row[4])
                map = common.toFloat(row[5])
                msrp = common.toFloat(row[6])

                # Measurement
                uom = common.toText(row[11]).title()
                minimum = 2

                # Tagging
                keywords = f"{row[10]} {collection} {usage} {description}"
                colors = color

                # Image
                thumbnail = row[24]

                # Status
                statusP = True
                statusS = False

                # Fine-tuning
                TYPE_DICT = {
                    "WP": "Wallpaper",
                    "FB": "Fabric"
                }
                type = TYPE_DICT.get(type, type)

                UOM_DICT = {
                    "R": "Roll",
                    "Y": "Yard",
                    "Yards": "Yard",
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
                'repeatV': repeatV,
                'repeatH': repeatH,

                'yardsPR': yardsPR,
                'match': match,
                'usage': usage,

                'features': features,

                'uom': uom,
                'minimum': minimum,

                'cost': cost,
                'map': map,
                'msrp': msrp,

                'keywords': keywords,
                'colors': colors,

                'thumbnail': thumbnail,

                'statusP': statusP,
                'statusS': statusS,
            }
            products.append(product)

        return products
