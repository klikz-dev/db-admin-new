from django.core.management.base import BaseCommand
from feed.models import PremierPrints

import os
import openpyxl

from utils import database, debug, common

BRAND = "Premier Prints"
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
                feeds=PremierPrints.objects.all(), private=True)

        if "image" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.downloadImages()


class Processor:
    def __init__(self):
        self.DatabaseManager = database.DatabaseManager(
            brand=BRAND, Feed=PremierPrints)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def fetchFeed(self):
        # Get Product Feed
        products = []

        wb = openpyxl.load_workbook(
            f"{FILEDIR}/premierprints-master.xlsx", data_only=True)
        sh = wb.worksheets[0]

        for row in sh.iter_rows(min_row=2, values_only=True):
            try:
                # Primary Keys
                mpn = common.toText(row[0])
                sku = f"DBP {mpn}"
                pattern = common.toText(row[4])
                color = common.toText(row[5])

                # Categorization
                brand = BRAND
                manufacturer = BRAND

                type = common.toText(row[3])
                collection = common.toText(row[2])

                # Main Information
                description = common.toText(row[9])
                width = common.toFloat(row[10])
                repeatH = common.toFloat(row[14])
                repeatV = common.toFloat(row[13])

                # Additional Information
                usage = common.toText(row[20])

                # Measurement
                uom = common.toText(row[19])
                minimum = 2

                # Pricing
                cost = common.toFloat(row[8])

                # Tagging
                keywords = f"{row[20]} {row[25]} {pattern}"
                colors = row[24]

                # Status
                statusP = True
                statusS = True

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
                'width': width,
                'repeatH': repeatH,
                'repeatV': repeatV,

                'usage': usage,

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
