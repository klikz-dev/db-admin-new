from django.core.management.base import BaseCommand
from feed.models import JaipurLiving

import os
import openpyxl

from utils import database, debug, common

BRAND = "Jaipur Living"
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
                src="/jaipur/Jaipur Living Master Data Template.xlsx",
                dst=f"{FILEDIR}/jaipurliving-master.xlsx",
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
            processor = Processor()
            processor.DatabaseManager.updateProducts(
                feeds=JaipurLiving.objects.all(), private=False)

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
            brand=BRAND, Feed=JaipurLiving)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def fetchFeed(self):
        # Get Product Feed
        products = []

        wb = openpyxl.load_workbook(
            f"{FILEDIR}/jaipurliving-master.xlsx", data_only=True)
        sh = wb.worksheets[0]

        for row in sh.iter_rows(min_row=2, values_only=True):
            try:
                # Primary Keys
                mpn = common.toText(row[7])
                sku = f"JL {mpn}"

                pattern = common.toText(row[13])
                if common.toText(row[53]):
                    pattern = f"{pattern} {common.toText(row[53])}"

                color = common.toText(row[56])
                if common.toText(row[57]):
                    color = f"{color} / {common.toText(row[57])}"

                name = common.toText(row[9]).title().replace(BRAND, "").strip()

                # Categorization
                brand = BRAND
                manufacturer = BRAND
                type = common.toText(row[0]).title()
                collection = common.toText(row[12])

                # Main Information
                description = row[25]
                width = common.toFloat(row[21])
                length = common.toFloat(row[22])
                height = common.toFloat(row[24])

                size = common.toText(row[18]).replace("X", " x ").replace(
                    "Folded", "").replace("BOX", "").replace("  ", " ").strip()

                # Additional Information
                front = common.toText(row[35])
                back = common.toText(row[36])
                filling = common.toText(row[37])

                material = f"Front: {front}"
                if back:
                    material += f", Back: {back}"
                if filling:
                    material += f", Filling: {filling}"

                care = common.toText(row[39])
                country = common.toText(row[32])
                upc = common.toInt(row[6])
                weight = common.toFloat(row[88])

                features = []
                for id in range(26, 32):
                    if row[id]:
                        features.append(common.toText(row[id]))

                # Measurement
                uom = "Item"

                # Pricing
                cost = common.toFloat(row[15])
                map = common.toFloat(row[16])
                msrp = common.toFloat(row[17])

                # Tagging
                keywords = ", ".join(
                    (row[19], row[50], row[51], pattern, name, description, type, ", ".join(features)))
                colors = color

                # Image
                thumbnail = row[89]
                if thumbnail == "http://cdn1-media.s3.us-east-1.amazonaws.com/product_links/Product_Images/":
                    thumbnail = f"{thumbnail}{str(row[8]).strip()}.jpg"

                roomsets = []
                for id in range(90, 104):
                    if row[id]:
                        roomsets.append(row[id])

                # Status
                if row[19] == "Swatches":
                    statusP = False
                else:
                    statusP = True
                statusS = False

                # Shipping
                shippingWidth = common.toFloat(row[86])
                shippingLength = common.toFloat(row[85])
                shippingHeight = common.toFloat(row[87])
                shippingWeight = common.toFloat(row[88])
                if shippingWidth > 95 or shippingLength > 95 or shippingHeight > 95 or shippingWeight > 40:
                    whiteGlove = True
                else:
                    whiteGlove = False

                # Fine-tuning
                name = f"{collection} {pattern} {color} {size} {type}"

                TYPE_DICT = {
                    "Accent Furniture": "Furniture",
                    "Décor": "Throw",
                }
                type = TYPE_DICT.get(type, type)

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

                'features': features,

                'uom': uom,

                'cost': cost,
                'map': map,
                'msrp': msrp,

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

        feeds = JaipurLiving.objects.all()
        for feed in feeds:
            stock = {
                'sku': feed.sku,
                'quantity': 5,
                'note': ""
            }
            stocks.append(stock)

        return stocks
