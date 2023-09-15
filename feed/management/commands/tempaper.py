from django.core.management.base import BaseCommand
from feed.models import Tempaper

import os
import xlrd

from utils import feed, debug, common

log, warn, error = debug.log, debug.warn, debug.error

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
                src="/tempaper/datasheets/tempaper-master.xlsx", dst=f"{FILEDIR}/tempaper-master.xlsx", fileSrc=True, delete=False)
            products = processor.fetchFeed()
            processor.feedManager.writeFeed(products=products)


class Processor:
    def __init__(self):
        self.feedManager = feed.FeedManager(brand=BRAND, Feed=Tempaper)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def fetchFeed(self):
        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/tempaper-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 3))
                sku = f"TP {mpn}"

                pattern = common.formatText(sh.cell_value(i, 4))
                color = common.formatText(sh.cell_value(i, 5))

                name = common.formatText(sh.cell_value(i, 8))

                # Categorization
                brand = BRAND
                type = common.formatText(sh.cell_value(i, 0))
                manufacturer = brand
                collection = common.formatText(sh.cell_value(i, 2))

                # Main Information
                description = common.formatText(sh.cell_value(i, 9))
                width = common.formatFloat(sh.cell_value(i, 17))
                length = common.formatFloat(sh.cell_value(i, 18)) * 12
                coverage = common.formatText(sh.cell_value(i, 21))

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
                yards = common.formatInt(sh.cell_value(i, 14))
                weight = common.formatFloat(sh.cell_value(i, 22))
                match = common.formatText(sh.cell_value(i, 25))
                material = common.formatText(sh.cell_value(i, 27))
                care = common.formatText(sh.cell_value(i, 32))
                country = common.formatText(sh.cell_value(i, 33))
                features = []
                for id in range(28, 30):
                    feature = common.formatText(sh.cell_value(i, id))
                    if feature:
                        features.append(feature)

                # Pricing
                cost = common.formatFloat(sh.cell_value(i, 10))
                map = common.formatFloat(sh.cell_value(i, 11))

                # Measurement
                uom = f"Per {common.formatText(sh.cell_value(i, 13))}"

                # Tagging
                colors = color
                tags = f"{material}, {match}, {sh.cell_value(i, 28)}, {sh.cell_value(i, 29)}, {collection}, {pattern}, {description}"

                # Image
                thumbnail = sh.cell_value(i, 34).replace("dl=0", "dl=1")

                roomsets = []
                for id in range(35, 39):
                    roomset = sh.cell_value(i, id).replace("dl=0", "dl=1")
                    if roomset != "":
                        roomsets.append(roomset)

                # Status
                statusP = True

                if type == "Wallpaper":
                    statusS = True
                else:
                    statusS = False

            except Exception as e:
                warn(BRAND, 1, str(e))
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
                'yards': yards,
                'weight': weight,
                'country': country,
                'match': match,
                'care': care,
                'features': features,

                'cost': cost,
                'map': map,
                'uom': uom,

                'tags': tags,
                'colors': colors,

                'thumbnail': thumbnail,
                'roomsets': roomsets,

                'statusP': statusP,
                'statusS': statusS,
            }
            products.append(product)

        return products
