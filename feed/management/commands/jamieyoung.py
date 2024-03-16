from django.core.management.base import BaseCommand
from feed.models import JamieYoung

import os
import environ
import openpyxl
import csv
import codecs

from utils import database, debug, common

env = environ.Env()

BRAND = "Jamie Young"
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
                feeds=JamieYoung.objects.all())

        if "image" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.downloadImages()


class Processor:
    def __init__(self):
        self.DatabaseManager = database.DatabaseManager(
            brand=BRAND, Feed=JamieYoung)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def fetchFeed(self):
        # Outlet
        outletMPNs = [
            "9CASPWHD131C",
            "5SHOR-PENA",
            "20KAI-BECA",
            "20SHEL-BEDO",
            "20WATE-CODG",
            "7LONG-BOGR",
            "7LONG-BOWH",
            "7LOTU-SMWH",
            "7MARB-XLWH"
        ]

        # Best Selling
        bestSellingPatterns = [
            "Rectangle Audrey",
            "Daybreak",
            "Chester Round Side Table",
            "Coco Pedestal",
            "Masonry",
            "Landslide",
            "Vapor",
            "Capital Rectangle",
            "Audrey Beaded",
            "Riviera Framed",
            "Maldives Framed",
            "Organic Round",
            "Watercolor",
            "Gilbert",
            "Serai",
            "Vapor Vase",
            "Kaya",
            "Agate Slice",
            "Evergreen Rectangle",
            "Lagoon",
            "Basketweave",
            "Kain Console",
            "Arch",
            "Mortar",
            "Willow",
            "Studio",
            "Flowering Lotus",
            "Oceane Gourd",
            "Batik",
            "Napa",
            "Barley Twist",
            "Amphora",
            "Farmhouse Bench",
            "Concentric",
            "Mirage Abstract",
            "Kain Side Table",
            "Vapor Single",
        ]

        # Available Items
        available_mpns = []
        f = open(f"{FILEDIR}/jamieyoung-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, 'ISO-8859-1'))
        for row in cr:
            if common.toInt(row[2]) > 0:
                available_mpns.append(row[1])

        # Get Product Feed
        products = []

        wb = openpyxl.load_workbook(
            f"{FILEDIR}/jamieyoung-master.xlsx", data_only=True)
        sh = wb.worksheets[0]

        for row in sh.iter_rows(min_row=2, values_only=True):
            try:
                # Primary Keys
                mpn = common.toText(row[0])
                sku = f"JY {mpn}"
                pattern = common.toText(row[2])
                color = common.toText(row[35])
                name = common.toText(row[3])

                # Categorization
                brand = BRAND
                manufacturer = BRAND
                type = common.toText(row[7]).title()
                collection = common.toText(row[4])

                # Main Information
                description = common.toText(row[26])
                width = common.toFloat(row[16])
                length = common.toFloat(row[14])
                height = common.toFloat(row[18])

                # Additional Information
                material = common.toText(row[34])
                care = common.toText(row[37])
                country = common.toText(row[46])
                weight = common.toFloat(row[12])
                disclaimer = common.toText(row[36])
                upc = common.toInt(row[1])

                dimension = common.toText(row[19])
                specs = [
                    ("Dimension", dimension),
                ]

                features = [str(row[id]).strip()
                            for id in range(28, 33) if row[id]]
                features.extend([str(row[id]).strip()
                                for id in range(38, 45) if row[id]])

                # Measurement
                uom = "Item"

                # Pricing
                cost = common.toFloat(row[8])
                map = common.toFloat(row[9])
                msrp = common.toFloat(row[10])

                # Tagging
                keywords = f"{row[19]}, {','.join(features)}, {collection}, {pattern}, {description}"
                colors = color

                # Image
                thumbnail = common.toText(row[69]).replace("dl=0", "dl=1")
                roomsets = [common.toText(row[id]).replace(
                    "dl=0", "dl=1") for id in range(70, 83) if row[id]]

                # Status
                statusP = not (
                    "Sideboard" in pattern or "Console" in pattern or mpn not in available_mpns)
                statusS = False
                bestSeller = pattern in bestSellingPatterns
                outlet = mpn in outletMPNs

                # Shipping
                shippingWidth = common.toFloat(
                    row[58]) + common.toFloat(row[62])
                shippingLength = common.toFloat(
                    row[57]) + common.toFloat(row[61])
                shippingHeight = common.toFloat(
                    row[59]) + common.toFloat(row[63])
                shippingWeight = common.toFloat(
                    row[56]) + common.toFloat(row[60])
                if shippingWidth > 95 or shippingLength > 95 or shippingHeight > 95 or shippingWeight > 40:
                    whiteGlove = True
                else:
                    whiteGlove = False

                # Fine-tuning
                TYPE_DICT = {
                    "Table Lamps": "Table Lamp",
                    "Floor Lamps": "Floor Lamp",
                    "Wall Sconces": "Wall Sconce",
                    "Chandeliers": "Chandelier",
                    "Pendants": "Pendant",
                    "Flush Mounts": "Flush Mount",
                    "Semi-Flush Mounts": "Semi-Flush Mount",
                    "Mirrors": "Mirror",
                    "Accessories": "Accessory",
                }
                type = TYPE_DICT.get(type, type)

                pattern = pattern.replace(type, "")

                pattern = pattern.replace(
                    "**MUST SHIP COMMON CARRIER**", "").replace("  ", " ").strip()
                name = name.replace(
                    "**MUST SHIP COMMON CARRIER**", "").replace("  ", " ").strip()

                # Exceptions
                if "Sideboard" in pattern or "Console" in pattern:
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
                'length': length,
                'height': height,

                'material': material,
                'care': care,
                'country': country,
                'weight': weight,
                'disclaimer': disclaimer,
                'upc': upc,

                'features': features,
                'specs': specs,

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
                'bestSeller': bestSeller,
                'outlet': outlet,
            }
            products.append(product)

        return products
