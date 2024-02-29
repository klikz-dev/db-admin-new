from django.core.management.base import BaseCommand
from feed.models import Surya

import os
import openpyxl

from utils import database, debug, common

BRAND = "Surya"
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
                src="/surya/surya_masterlist_dbest.xlsx",
                dst=f"{FILEDIR}/surya-master.xlsx",
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
            feeds = Surya.objects.filter(pattern="ZRZ-2317")

            processor = Processor()
            processor.DatabaseManager.updateProducts(feeds=feeds)

        if "image" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.downloadImages()


class Processor:
    def __init__(self):
        self.DatabaseManager = database.DatabaseManager(
            brand=BRAND, Feed=Surya)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def fetchFeed(self):
        # Get Product Feed
        products = []

        wb = openpyxl.load_workbook(f"{FILEDIR}/surya-master.xlsx")
        sh = wb.worksheets[0]

        for row in sh.iter_rows(min_row=2, values_only=True):
            try:
                # Primary Keys
                mpn = common.toText(row[2])

                sku = f"SR {mpn}"
                pattern = common.toText(row[3])
                color = ' '.join(common.toText(row[12]).split(', ')[:2])

                name = common.toText(row[4])

                # Categorization
                brand = BRAND
                type = common.toText(row[0])
                manufacturer = BRAND
                collection = common.toText(row[5])

                # Main Information
                description = common.toText(row[6])
                width = common.toFloat(row[19])
                length = common.toFloat(row[20])
                height = common.toFloat(row[18])

                if length == 0 and height != 0:
                    length = height
                    height = 0

                size = common.toText(row[16])

                # Additional Information
                material = common.toText(row[13])
                care = common.toText(row[71])
                country = common.toText(row[28])
                upc = common.toInt(row[8])
                weight = common.toFloat(row[21]) or 5

                specs = [
                    ("Colors", common.toText(row[12])),
                    ("Weight", f"{weight} lbs"),
                ]

                # Measurement
                uom = "Item"

                # Pricing
                cost = common.toFloat(row[9])
                map = common.toFloat(row[10])

                # Tagging
                keywords = f"{common.toText(row[14])}, {common.toText(row[41])}, {type}, {collection}, {pattern}"
                if common.toText(row[31]) == "Yes":
                    keywords = f"{keywords}, Outdoor"

                colors = common.toText(row[12])

                # Status
                statusP = True
                statusS = False

                if common.toText(row[30]) == "Yes":
                    bestSeller = True
                else:
                    bestSeller = False

                # Image
                thumbnail = row[92]

                roomsets = []
                for id in range(93, 99):
                    if row[id] != "":
                        roomsets.append(row[id])

                # Shipping
                shippingHeight = common.toFloat(row[24])
                shippingWidth = common.toFloat(row[25])
                shippingDepth = common.toFloat(row[23])
                shippingWeight = common.toFloat(row[22])
                if shippingWidth > 95 or shippingHeight > 95 or shippingDepth > 95 or shippingWeight > 40:
                    whiteGlove = True
                else:
                    whiteGlove = False

                # Type Mapping & Exceptions
                if cost == 0:
                    continue

                if not type or "Swatch" in type:
                    continue

                type_mapping = {
                    "Rugs": "Rug",
                    "Wall Hangings": "Wall Hanging",
                    "Mirrors": "Mirror",
                    "Bedding": "Bed",
                    "Wall Art - Stock": "Wall Art",
                    "Throws": "Throw",
                    "Ceiling Lighting": "Lighting",
                    "Accent and Lounge Chairs": "Accent Chair",
                    "Decorative Accents": "Decorative Accent",
                    "Sofas": "Sofa",
                    "Wall Sconces": "Wall Sconce",
                    "Rug Blanket": "Rug",
                    "Bedding Inserts": "Bed",
                    "Made to Order Rugs": "Rug",
                    "Printed Rug Set (3pc)": "Rug",
                }

                if type in type_mapping:
                    type = type_mapping[type]

                # Rewrite Name
                name = f"{collection} {pattern} {color} {size} {type}"

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
                'size': size,

                'material': material,
                'care': care,
                'country': country,
                'weight': weight,
                'upc': upc,

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
                'bestSeller': bestSeller
            }
            products.append(product)

        return products
