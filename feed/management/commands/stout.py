from django.core.management.base import BaseCommand
from feed.models import Stout

import os
import environ
import openpyxl
import requests
import json

from utils import database, debug, common

env = environ.Env()

BRAND = "Stout"
FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "feed" in options['functions']:
            common.downloadFileFromLink(
                "https://www.stouttextiles.com/downloads/Online_Retail_Items.xlsx",
                f"{FILEDIR}/stout-master.xlsx"
            )

            processor = Processor()
            feeds = processor.fetchFeed()
            processor.DatabaseManager.writeFeed(feeds=feeds)

        if "validate" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.validateFeed()

        if "status" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.statusSync(fullSync=True)

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
                feeds=Stout.objects.all())

        if "image" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.downloadImages()

        if "inventory" in options['functions']:
            processor = Processor()
            stocks = processor.inventory()
            processor.DatabaseManager.updateInventory(
                stocks=stocks, type=1, reset=True)


class Processor:
    def __init__(self):
        self.DatabaseManager = database.DatabaseManager(
            brand=BRAND, Feed=Stout)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def requestAPI(self, mpn):
        try:
            responseData = requests.post(
                env('STOUT_API_URL'),
                data={
                    'id': mpn,
                    'key': env('STOUT_API_KEY')
                }
            )
            responseJSON = json.loads(responseData.text)
            result = responseJSON["result"][0]

            return result
        except Exception as e:
            debug.warn(BRAND, str(e))
            return None

    def fetchFeed(self):
        # Get Product Feed
        products = []

        wb = openpyxl.load_workbook(
            f"{FILEDIR}/stout-master.xlsx", data_only=True)
        sh = wb.worksheets[0]

        for row in sh.iter_rows(min_row=2, values_only=True):
            try:
                # Primary Keys
                mpn = common.toText(row[0])

                debug.log(BRAND, f"Fetching data for {mpn}")
                data = self.requestAPI(mpn)

                sku = f"STOUT {mpn}"

                pattern = common.toText(row[1].split(" ")[0])
                color = common.toText(row[8])

                # Categorization
                brand = BRAND
                manufacturer = BRAND

                type = common.toText(row[14]).title()

                collection = common.toText(row[19])

                # Main Information
                width = common.toFloat(row[4])
                repeatV = common.toFloat(row[5])
                repeatH = common.toFloat(row[6])

                # Additional Information
                usage = type
                content = str(row[7]).replace(
                    " ", ", ").replace("%", "% ").strip()
                finish = common.toText(row[13])
                country = common.toText(row[15])

                construction = common.toText(row[10])
                style = common.toText(row[11])
                specs = [
                    ("Construction", construction),
                    ("Style", style),
                ]

                features = [row[12]] if row[12] else []

                # Measurement
                uom = str(data.get("uom", "")).title()

                # Pricing
                cost = common.toFloat(
                    data.get("price", 0)) or common.toFloat(row[2])
                map = common.toFloat(data.get("map", 0))
                msrp = common.toFloat(row[3])

                # Tagging
                keywords = f"{construction} {style}"
                colors = color

                # Image
                thumbnail = f"https://cdn.estout.com/Images/{mpn}.jpg"

                # Status
                phase = common.toInt(data.get("phase", ""))

                statusP = phase in (0, 1, 2)
                statusS = phase in (0, 1)

                # Fine-tuning
                if "Trimming" in type or "Trimming" in construction or "Trimming" in style:
                    type = "Trim"
                elif "Wallcovering" in type or "Wallcovering" in construction or "Wallcovering" in style:
                    type = "Wallpaper"
                else:
                    type = "Fabric"

                name = f"{pattern} {color} {type}"

                # Exceptions
                # if cost == 0 or not pattern or not color or not type:
                #     continue

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

                'width': width,
                'repeatV': repeatV,
                'repeatH': repeatH,

                'usage': usage,
                'content': content,
                'finish': finish,
                'country': country,

                'specs': specs,
                'features': features,

                'uom': uom,

                'cost': cost,
                'map': map,
                'msrp': msrp,

                'keywords': keywords,
                'colors': colors,

                'thumbnail': thumbnail,

                'statusP': statusP,
                'statusS': statusS,
            }
            products.append(product)

        return products

    def inventory(self):
        stocks = []

        products = Stout.objects.filter(statusP=True)
        for product in products:
            mpn = product.mpn
            sku = product.sku

            try:
                data = self.requestAPI(mpn)

                stockP = common.toInt(data["avail"])

                print(sku, stockP)

                stock = {
                    'sku': sku,
                    'quantity': stockP,
                    'note': ""
                }
                stocks.append(stock)
            except Exception as e:
                continue

        return stocks
