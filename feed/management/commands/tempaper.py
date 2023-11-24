from django.core.management.base import BaseCommand
from feed.models import Tempaper

import os
import openpyxl

from utils import database, debug, common

BRAND = "Tempaper"
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
                src="/tempaper/datasheets/tempaper-master.xlsx",
                dst=f"{FILEDIR}/tempaper-master.xlsx",
                fileSrc=True,
                delete=False
            )
            products = processor.fetchFeed()
            processor.DatabaseManager.writeFeed(products=products)
            # processor.DatabaseManager.validateFeed(products=products)

        if "sync" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.statusSync()


class Processor:
    def __init__(self):
        self.DatabaseManager = database.DatabaseManager(
            brand=BRAND, Feed=Tempaper)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def fetchFeed(self):
        # Get Product Feed
        products = []

        wb = openpyxl.load_workbook(f"{FILEDIR}/tempaper-master.xlsx")
        sh = wb.worksheets[0]

        for row in sh.iter_rows(min_row=2, values_only=True):
            try:
                # Primary Keys
                mpn = common.toText(row[3])
                sku = f"TP {mpn}"

                pattern = common.toText(row[4])
                color = common.toText(row[5])

                name = common.toText(row[8])

                # Categorization
                brand = BRAND
                type = common.toText(row[0])
                manufacturer = brand
                collection = common.toText(row[2])

                # Main Intoion
                description = common.toText(row[9])
                width = common.toFloat(row[17])
                length = common.toFloat(row[18]) * 12
                coverage = common.toText(row[21])

                specs = [
                    ("Width", f"{round(width / 36, 2)} yd ({width} in)"),
                    ("Length", f"{round(length / 36, 2)} yd ({length} in)"),
                    ("Coverage", coverage),
                ]

                if type == "Rug":
                    specs = []
                    dimension = coverage
                else:
                    width = 0
                    length = 0
                    dimension = ""

                # Additional Information
                yardsPR = common.toInt(row[14])
                weight = common.toFloat(row[22])
                match = common.toText(row[25])
                material = common.toText(row[27])
                care = common.toText(row[32])
                country = common.toText(row[33])
                features = []
                for id in range(28, 30):
                    feature = common.toText(row[id])
                    if feature:
                        features.append(feature)

                # Pricing
                cost = common.toFloat(row[10])
                map = common.toFloat(row[11])

                # Measurement
                uom = f"Per {common.toText(row[13])}"

                # Tagging
                colors = color
                keywords = f"{material}, {match}, {common.toText(row[28])}, {common.toText(row[29])}, {collection}, {pattern}, {description}"

                # Image
                thumbnail = common.toText(row[34]).replace("dl=0", "dl=1")

                roomsets = []
                for id in range(35, 39):
                    roomset = common.toText(row[id]).replace("dl=0", "dl=1")
                    if roomset != "":
                        roomsets.append(roomset)

                # Status
                statusP = True

                if type == "Wallpaper":
                    statusS = True
                else:
                    statusS = False

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
                'dimension': dimension,

                'material': material,
                'yardsPR': yardsPR,
                'weight': weight,
                'country': country,
                'match': match,
                'care': care,
                'features': features,

                'cost': cost,
                'map': map,
                'uom': uom,

                'keywords': keywords,
                'colors': colors,

                'thumbnail': thumbnail,
                'roomsets': roomsets,

                'statusP': statusP,
                'statusS': statusS,
            }
            products.append(product)

        return products
