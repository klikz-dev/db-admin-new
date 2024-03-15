from django.core.management.base import BaseCommand
from feed.models import Scalamandre

import os
import requests
import json
import environ

from utils import database, debug, common

env = environ.Env()

BRAND = "Scalamandre"
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
                feeds=Scalamandre.objects.all())

        if "image" in options['functions']:
            processor = Processor()
            processor.DatabaseManager.downloadImages()


class Processor:
    def __init__(self):
        self.DatabaseManager = database.DatabaseManager(
            brand=BRAND, Feed=Scalamandre)

        responseData = requests.post(
            f"{env('SCALA_API_URL')}/Auth/authenticate",
            headers={'Content-Type': 'application/json'},
            data=json.dumps({
                "Username": env('SCALA_API_USERNAME'),
                "Password": "EuEc9MNAvDqvrwjgRaf55HCLr8c5B2^Ly%C578Mj*=CUBZ-Y4Q5&Sc_BZE?n+eR^gZzywWphXsU*LNn!",
            })
        )
        responseJSON = json.loads(responseData.text)
        self.token = responseJSON['Token']

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def requestAPI(self, url):
        try:
            responseData = requests.get(
                f"{env('SCALA_API_URL')}/{url}",
                headers={'Authorization': 'Bearer {}'.format(self.token)}
            )
            responseJSON = json.loads(responseData.text)

            return responseJSON
        except Exception as e:
            debug.warn(BRAND, str(e))
            return None

    def fetchFeed(self):
        # Get Product Feed
        products = []

        productsData = self.requestAPI("ScalaFeedAPI/FetchProductsFeed")

        for row in productsData['FEEDPRODUCTS']:
            # print(row)
            try:
                # Primary Keys
                mpn = row['ITEMID']
                sku = f"SCALA {row['SKU']}"
                pattern = common.toText(
                    row['PATTERN_DESCRIPTION'].replace('PILLOW', '')).title()
                color = common.toText(row['COLOR']).title()

                # Categorization
                brand = BRAND
                manufacturer = common.toText(row['BRAND'])
                type = common.toText(row['CATEGORY'])
                collection = common.toText(row.get('WEB COLLECTION NAME', ''))

                # Main Information
                description = common.toText(row['DESIGN_INSPIRATION'])
                width = common.toFloat(row['WIDTH'])
                size = common.toText(row['PIECE SIZE'])
                repeatV = common.toFloat(row['PATTERN REPEAT LENGTH'])
                repeatH = common.toFloat(row['PATTERN REPEAT WIDTH'])

                # Additional Information
                yardsPR = common.toFloat(row['YARDS PER ROLL'])
                content = common.toText(row.get('FIBER CONTENT', '')).title()
                material = common.toText(row.get('MATERIALTYPE', '')).title()
                usage = common.toText(row['WEARCODE']).title()

                # Measurement
                minimum = common.toInt(row['MIN ORDER']
                                       .split(' ')[0] if row['MIN ORDER'] else 1)
                increment = common.toInt(row['WEB SOLD BY'])

                uom = common.toText(row['UNITOFMEASURE'])

                # Pricing
                cost = common.toFloat(row['NETPRICE'])

                # Tagging
                keywords = f"{collection} {row.get('WEARCODE', '')} {material} {description}"
                colors = color

                # Status
                statusP = True
                statusS = True

                if row.get('DISCONTINUED', False) != False:
                    statusP = False
                    statusS = False
                if row.get('WEBENABLED', '') not in ["Y", "S"]:
                    statusP = False
                    statusS = False
                if row.get('IMAGEVALID', False) != True:
                    statusP = False
                    statusS = False
                if manufacturer in ["Tassinari & Chatel", "Lelievre", "Nicolette Mayer", "Jean Paul Gaultier"]:
                    statusP = False
                    statusS = False

                if type == "Pillow" or pattern == "NOBEL":
                    statusS = False

                # Fine-tuning
                TYPE_DICT = {
                    "WALLCOVERING": "Wallpaper",
                    "TRIMMING": "Trim",
                    "PILLOWS": "Pillow",
                    "FABRIC": "Fabric"
                }
                type = TYPE_DICT.get(type, type)

                MANUFACTURER_DICT = {
                    "The House of Scalamandré": "Scalamandre",
                    "LAMPSHADES": "Scalamandre",
                    "THIRD FLOOR FABRIC": "Scalamandre",
                    "WALLCOVERING": "Scalamandre"
                }
                manufacturer = MANUFACTURER_DICT.get(
                    manufacturer, manufacturer)

                UOM_DICT = {
                    "RL": "Roll",
                    "DR": "Double Roll",
                    "YD": "Yard",
                    "LY": "Yard",
                    "EA": "Item",
                    "PC": "Item",
                    "SF": "Square Foot",
                    "ST": "Set",
                    "PN": "Panel",
                    "TL": "Tile"
                }
                uom = UOM_DICT.get(uom, 'Item')

                name = f"{pattern} {color} {type}".title()

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
                'size': size,
                'repeatV': repeatV,
                'repeatH': repeatH,

                'yardsPR': yardsPR,
                'content': content,
                'material': material,
                'usage': usage,

                'uom': uom,
                'minimum': minimum,
                'increment': increment,

                'cost': cost,

                'keywords': keywords,
                'colors': colors,

                'statusP': statusP,
                'statusS': statusS,
            }
            products.append(product)

        return products
