from django.core.management.base import BaseCommand
from feed.models import PhillipsCollection

import os
import requests
import json
import environ
import time

from utils import database, debug, common

env = environ.Env()

BRAND = "Phillips Collection"
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
            brand=BRAND, Feed=PhillipsCollection)

        responseData = requests.post(
            f"{env('PHILLIPS_API_URL')}/auth",
            headers={
                'Content-type': 'application/json',
                'x-api-key': env('PHILLIPS_API_KEY')
            },
            data=json.dumps({
                "email": env('PHILLIPS_API_USERNAME'),
                "password": env('PHILLIPS_API_PASSWORD')
            })
        )
        responseJSON = json.loads(responseData.text)
        self.token = responseJSON['data']['token']

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def requestAPI(self, url):
        try:
            responseData = requests.get(
                f"{env('PHILLIPS_API_URL')}/{url}",
                headers={
                    'x-api-key': env('PHILLIPS_API_KEY'),
                    'Authorization': f"Bearer {self.token}"
                }
            )
            responseJSON = json.loads(responseData.text)

            return responseJSON['data']
        except Exception as e:
            debug.warn(BRAND, str(e))
            return None

    def fetchFeed(self):
        # Get Product Types
        types = {}
        typesData = self.requestAPI('items-categories?page_size=100')
        for type in typesData:
            types[type['_id']] = type['name']

        # Get Product Collections
        collections = {}
        collectionsData = self.requestAPI('items-collections?page_size=100')
        for collection in collectionsData:
            collections[collection['_id']] = collection['name']

        # Get Product Feed
        products = []

        page = 1

        while True:
            productsData = self.requestAPI(
                f"ecomm/items?page={page}&page_size=100")

            if len(productsData):
                for row in productsData:
                    try:
                        attr = row['description']

                        # Primary Keys
                        mpn = common.toText(row['_id'])
                        sku = f"PC {mpn}"

                        pattern = common.toText(row['desc'])
                        color = common.toText(row['descspec'].replace(
                            ",", "")) or common.toText(attr['color'][0])

                        # Categorization
                        brand = BRAND
                        manufacturer = BRAND

                        type = types.get(row['class']['category'], "Accent")

                        collection = next((collections.get(
                            c) for c in row['class']['collection'] if collections.get(c) is not None), "")

                        # Main Information
                        description = common.toText(attr['story'])
                        width = common.toFloat(attr['sizew'])
                        length = common.toFloat(attr['sizel'])
                        height = common.toFloat(attr['sizeh'])

                        # Additional Information
                        material = ", ".join(attr['material'] + attr['addmat'])
                        finish = ", ".join(attr['finish'])
                        care = common.toText(attr['care']).replace("\n", " ")
                        country = common.toText(row.get('countryoforigin', ''))
                        weight = common.toFloat(attr['weight'])
                        upc = common.toText(row['upc'])
                        disclaimer = common.toText(attr['disclaimer'])

                        features = attr['features']

                        # Measurement
                        uom = common.toText(row['price']['uom']).title()
                        minimum = common.toInt(row['price']['factor'])

                        # Tagging
                        keywords = f"{collection} {pattern} {description} {type} {attr['style']}"
                        colors = " ".join(attr['color'])

                        # Pricing
                        cost = common.toFloat(row['price']['price'])
                        msrp = common.toFloat(row['msrp'])
                        map = common.toFloat(row['map'])

                        # Image
                        thumbnail = row['assets']['images']['main']
                        roomsets = []
                        for roomset in row['assets']['images']['details']:
                            roomsets.append(roomset['url'])
                        for roomset in row['assets']['images']['lifestyle']:
                            roomsets.append(roomset['url'])

                        # Availability
                        if row['status'] == "ACTIVE":
                            statusP = True
                        else:
                            statusP = False

                        statusS = False

                        # Shipping
                        shippingWidth = common.toFloat(attr['packw'])
                        shippingLength = common.toFloat(attr['packl'])
                        shippingHeight = common.toFloat(attr['packh'])
                        shippingWeight = common.toFloat(attr['packwght'])
                        if shippingWidth > 95 or shippingLength > 95 or shippingHeight > 95 or shippingWeight > 40:
                            whiteGlove = True
                        else:
                            whiteGlove = False

                        if row['settings']['stocking'] == True and row['qtyavailable'] > 0:
                            quickShip = True
                        else:
                            quickShip = False

                        # Fine-tuning
                        TYPE_DICT = {
                            "Side Tables": "Side Table",
                            "Pedestals": "Accent",
                            "Figures": "Accent",
                            "Wall Tiles": "Wall Art",
                            "Animals": "Accent",
                            "Hanging Lamps": "Accent Lamp",
                            "Mirrors": "Mirror",
                            "Coffee Tables": "Coffee Table",
                            "Dimensional": "Accent",
                            "Table Lamps": "Table Lamp",
                            "Dining Tables": "Dining Table",
                            "Consoles / Sofa Tables": "Console",
                            "Floor Lamps": "Floor Lamp",
                            "Abstract": "Accent",
                            "Framed": "Accent",
                            "Bowls / Vessels": "Bowl",
                            "Objects": "Object",
                            "Screens": "Screen",
                            "Vases": "Vase",
                            "Planters": "Planter",
                            "Desks": "Desk",
                            "Seating": "Chair",
                            "Other": "Accent",
                            "Stools": "Stool",
                            "Benches": "Bench",
                            "Bar": "Bar Stool",
                        }
                        type = TYPE_DICT.get(type, type)

                        pattern = pattern.replace(type, "").strip()

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
                        'height': height,

                        'material': material,
                        'finish': finish,
                        'care': care,
                        'weight': weight,
                        'country': country,
                        'upc': upc,
                        'disclaimer': disclaimer,

                        'features': features,

                        'uom': uom,
                        'minimum': minimum,

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
                        'quickShip': quickShip,
                    }
                    products.append(product)

                page += 1
            else:
                break

        return products

    def inventory(self):
        stocks = []

        products = PhillipsCollection.objects.filter(statusP=True)
        for product in products:
            mpn = product.mpn
            sku = product.sku

            try:
                data = self.requestAPI(f"ecomm/items/{mpn}/inventory")

                stockP = common.toInt(data["qtyavailable"])

                data = self.requestAPI(f"ecomm/items/{mpn}/leadtime")

                stockNote = common.toText(data['leadtime'][0]['message'])

                print(sku, stockP, stockNote)

                stock = {
                    'sku': sku,
                    'quantity': stockP,
                    'note': stockNote
                }
                stocks.append(stock)

                time.sleep(0.5)

            except Exception as e:
                continue

        return stocks
