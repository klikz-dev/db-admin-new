from django.core.management.base import BaseCommand
from feed.models import Kravet

import os
import environ
import csv
import codecs
import re

from utils import database, debug, common

env = environ.Env()

BRAND = "Kravet"
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
                feeds=Kravet.objects.all())

        if "image" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.downloadImages()


class Processor:
    def __init__(self):
        self.DatabaseManager = database.DatabaseManager(
            brand=BRAND, Feed=Kravet)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def fetchFeed(self):
        # Get Product Feed
        products = []

        f = open(f"{FILEDIR}/kravetdecor-master.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
        for row in cr:
            if row[0] == "sku":
                continue

            try:
                # Primary Keys
                mpn = common.toText(row[0])
                sku = f"KD {mpn.replace('.0', '').replace('.', '-')}"

                pattern = common.toText(row[1]).replace(",", "")
                color = sku.split("-")[2].title()

                # Categorization
                brand = BRAND
                manufacturer = f"{BRAND} Decor"
                type = common.toText(row[6]).title()
                collection = common.toText(row[3])

                # Main Information
                description = common.toText(row[2])
                width = common.toFloat(row[11])
                length = common.toFloat(row[10])
                height = common.toFloat(row[12])

                # Additional Information
                usage = common.toText(row[5])
                material = common.toText(row[20])
                care = common.toText(row[24])
                country = common.toText(row[21])
                weight = common.toFloat(row[14])
                upc = common.toText(row[34])

                features = [row[25]] if row[25] else []

                # Measurement
                uom = "Item"

                # Pricing
                cost = common.toFloat(row[15])

                # Tagging
                keywords = f"{row[6]} {usage} {pattern} {collection} {description}"
                colors = row[7]

                # Image
                thumbnail = row[35]

                roomsets = [row[id] for id in range(36, 40) if row[id]]

                # Status
                statusP = row[4] == "Active"
                statusS = False

                whiteGlove = "White Glove" in row[17]

                # Fine-tuning
                type = type[:-1] if type.endswith('s') else type
                TYPE_DICT = {
                    "Boxe": "Box",
                    "Benches & Ottoman": "Ottoman"
                }
                type = TYPE_DICT.get(type, type)

                pattern = re.sub(
                    r'\s+', ' ', pattern.replace(type, "")).strip()

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
                'length': length,

                'usage': usage,
                'material': material,
                'care': care,
                'country': country,
                'weight': weight,
                'upc': upc,

                'features': features,

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
