from django.core.management.base import BaseCommand
from feed.models import ElaineSmith

import os
import openpyxl
import re

from utils import database, debug, common

BRAND = "Elaine Smith"
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
                feeds=ElaineSmith.objects.all(), private=False)

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
            brand=BRAND, Feed=ElaineSmith)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def fetchFeed(self):
        # Get Product Feed
        products = []

        wb = openpyxl.load_workbook(
            f"{FILEDIR}/elainesmith-master.xlsx", data_only=True)
        sh = wb.worksheets[0]

        for row in sh.iter_rows(min_row=2, values_only=True):
            try:
                mpn = common.toText(row[0])
                sku = f"ES {mpn}"

                pattern = common.toText(row[1])
                color = common.toText(row[16])

                # Categorization
                brand = BRAND
                manufacturer = BRAND
                type = "Pillow"
                collection = pattern

                # Main Information
                description = common.toText(row[15])
                size = common.toText(row[2])

                # Measurement
                uom = "Item"

                # Pricing
                cost = common.toFloat(row[4])
                map = common.toFloat(row[5])
                msrp = common.toFloat(row[6])

                # Tagging
                keywords = f"{collection} {pattern} {description} {row[17]} {row[18]}"
                colors = color

                # Image
                thumbnail = row[7]
                roomsets = [row[id] for id in range(8, 15) if row[id]]

                # Status
                statusP = True
                statusS = False

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
                'size': size,

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
            }
            products.append(product)

        return products

    def inventory(self):
        stocks = []

        feeds = ElaineSmith.objects.all()
        for feed in feeds:
            stock = {
                'sku': feed.sku,
                'quantity': 5,
                'note': ""
            }
            stocks.append(stock)

        return stocks
