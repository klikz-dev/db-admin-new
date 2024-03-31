from django.core.management.base import BaseCommand
from feed.models import Schumacher

import os
import environ
import requests
import csv
import codecs

from utils import database, debug, common

env = environ.Env()

BRAND = "Schumacher"
FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "feed" in options['functions']:
            processor = Processor()
            processor.downloadFeed()
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
                feeds=Schumacher.objects.all())

        if "image" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.downloadImages()

        if "inventory" in options['functions']:
            processor = Processor()
            processor.downloadFeed()
            stocks = processor.inventory()
            processor.DatabaseManager.updateInventory(
                stocks=stocks, type=1, reset=True)


class Processor:
    def __init__(self):
        self.DatabaseManager = database.DatabaseManager(
            brand=BRAND, Feed=Schumacher)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def downloadFeed(self):
        response = requests.request(
            "GET",
            f"{env('SCH_API_URL')}?type=1",
            headers={
                'apiKey': env('SCH_API_KEY')
            }
        )

        if response.status_code == 200:
            with open(f"{FILEDIR}/schumacher-master.csv", 'w', encoding='utf-8') as csv_file:
                csv_file.write(response.text)
                debug.log(
                    BRAND, "Downloaded schumacher-master.csv successfully. ")
        else:
            debug.warn(
                BRAND, f"Failed to fetch data: {response.status_code}")

    def fetchFeed(self):
        # Sample Status
        discontinuedSamples = []

        f = open(f"{FILEDIR}/schumacher-sample-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
        for row in cr:
            mpn = common.toText(row[0])
            stockS = common.toInt(row[1])
            if stockS < 1:
                discontinuedSamples.append(mpn)

        # Get Product Feed
        products = []

        f = open(f"{FILEDIR}/schumacher-master.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))

        for row in cr:
            if row[0] == "Category":
                continue

            try:
                # Primary Keys
                mpn = common.toText(row[3])
                sku = f"SCH {mpn}"

                pattern = common.toText(row[4]).title()
                color = common.toText(row[5]).title()

                # Categorization
                brand = BRAND
                manufacturer = BRAND
                type = common.toText(row[0]).title()
                collection = common.toText(row[2]).title()

                # Main Information
                description = common.toText(row[17])
                width = common.toFloat(row[11].split("(")[0])
                length = common.toFloat(row[21].split("(")[0])
                repeatV = common.toFloat(row[15].split("(")[0])
                repeatH = common.toFloat(row[16].split("(")[0])

                # Additional Information
                yardsPR = common.toFloat(row[8])
                match = common.toText(row[14])

                content_parts = [common.toText(row[12]) if row[12] else "", common.toText(
                    row[13]) if row[13] else ""]
                content = ", ".join(filter(None, content_parts))

                # Measurement
                uom = common.toText(row[9]).title()
                minimum = common.toInt(row[10])
                increment = minimum if type == "Wallpaper" and minimum > 1 else 1

                # Pricing
                cost = common.toFloat(row[7])

                # Tagging
                keywords = f"{collection} {pattern} {description} {row[6]}"
                colors = color

                # Image
                thumbnail = common.toText(row[18]).strip()
                roomsets = common.toText(row[22]).split(",")

                # Fine-tuning
                if "BORÅSTAPETER" in collection:
                    manufacturer = "Borastapeter"
                    collection = "Borastapeter"
                else:
                    collection = collection.replace(
                        "Collection Name", "").strip()

                if collection == "Rug Pads":
                    type = "Rug Pad"

                TYPE_DICT = {
                    "Wallcovering": "Wallpaper",
                    "Rugs & Carpets": "Rug",
                    "Furniture & Accessories": "Pillow",
                }
                type = TYPE_DICT.get(type, type)

                UOM_DICT = {
                    "Single Roll": "Roll",
                    "Yd": "Yard"
                }
                uom = UOM_DICT.get(uom, "Item")

                pattern = pattern.replace(type, "").strip()

                width = width * 12 if "'" in row[11] else width
                length = length * 12 if "'" in row[21] else length

                if type == "Rug" or type == "Rug Pad":
                    size = f"{common.toFloat(width / 12)}' x {common.toFloat(length / 12)}'"
                    name = f"{pattern} {color} {size} {type}"
                elif type == "Pillow":
                    size = f'{width}" x {length}"'
                    name = f"{pattern} {color} {size} {type}"
                else:
                    size = ""
                    name = f"{pattern} {color} {type}"

                # Exceptions
                if cost == 0 or not pattern or not color or not type:
                    continue

                # Status
                statusP = not (type == "Rug" and cost == 15)
                statusS = type in ["Wallpaper", "Fabric", "Trim"]

                if mpn in discontinuedSamples:
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
                'width': width,
                'length': length,
                'size': size,
                'repeatV': repeatV,
                'repeatH': repeatH,

                'yardsPR': yardsPR,
                'match': match,
                'content': content,

                'uom': uom,
                'minimum': minimum,
                'increment': increment,

                'cost': cost,

                'keywords': keywords,
                'colors': colors,

                'thumbnail': thumbnail,
                'roomsets': roomsets,

                'statusP': statusP,
                'statusS': statusS,
            }
            products.append(product)

        return products

    def inventory(self):
        stocks = []

        f = open(f"{FILEDIR}/schumacher-master.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
        for row in cr:
            if row[0] == "Category":
                continue

            mpn = common.toText(row[3])

            try:
                product = Schumacher.objects.get(mpn=mpn)
            except Schumacher.DoesNotExist:
                continue

            sku = product.sku
            stockP = common.toInt(row[19])

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': ""
            }
            stocks.append(stock)

        return stocks
