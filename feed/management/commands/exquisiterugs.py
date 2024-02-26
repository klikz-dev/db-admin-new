from django.core.management.base import BaseCommand
from feed.models import ExquisiteRugs

import os
import openpyxl

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

        if "update" in options['functions']:
            feeds = ExquisiteRugs.objects.filter(pattern="3153")

            processor = Processor()
            processor.DatabaseManager.updateProducts(feeds=feeds)

        if "image" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.downloadImages()


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

        wb = openpyxl.load_workbook(f"{FILEDIR}/exquisiterugs-master.xlsx")
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
                manufacturer = brand
                collection = common.toText(row[1])

                # Main Information
                description = common.toText(row[19])

                width = common.toFloat(row[15])
                length = common.toFloat(row[16])
                height = common.toFloat(row[17])

                specs = [
                    ("Dimension", common.toText(row[18])),
                ]

                # Additional Information
                material = common.toText(row[12])
                care = common.toText(row[25])
                weight = common.toFloat(row[14])
                country = common.toText(row[35])
                disclaimer = common.toText(row[24])
                upc = common.toInt(row[13])

                # Pricing
                cost = common.toFloat(row[7])
                map = common.toFloat(row[8])

                # Measurement
                uom = "Item"

                # Tagging
                keywords = f"{row[11]}, {material}"
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
                'width': width,
                'length': length,
                'height': height,
                'disclaimer': disclaimer,
                'upc': upc,

                'material': material,
                'care': care,
                'weight': weight,
                'country': country,

                'cost': cost,
                'map': map,

                'uom': uom,

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
