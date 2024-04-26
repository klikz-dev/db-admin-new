from django.core.management.base import BaseCommand
from feed.models import York

import os
import requests
import json
import re
import environ

from utils import database, debug, common
from vendor.models import Product

env = environ.Env()

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"
IMAGEDIR = f"{os.path.expanduser('~')}/admin/vendor/management/files/images"

BRAND = "York"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "test" in options['functions']:
            processor = Processor()
            processor.testData()

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
            processor.image()

        if "inventory" in options['functions']:
            processor = Processor()
            stocks = processor.inventory()
            processor.DatabaseManager.updateInventory(
                stocks=stocks, type=1, reset=True)


class Processor:
    def __init__(self):
        self.DatabaseManager = database.DatabaseManager(
            brand=BRAND, Feed=York)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def requestAPI(self, url):
        try:
            responseData = requests.get(f"{env('YORK_API_URL')}/{url}")
            responseJSON = json.loads(responseData.text)

            if "error" in responseJSON:
                return []
            else:
                return responseJSON['results']

        except Exception as e:
            debug.warn(BRAND, str(e))
            return None

    def testData(self):
        product = self.requestAPI("product.php/VG4415")
        print(product[0])

    def fetchFeed(self):
        # Get Product Feed
        products = []

        collections = self.requestAPI("collections.php")

        for collectionData in collections:
            collectionID = collectionData['collectionID']
            collectionName = collectionData['name']

            if collectionID == "":
                continue

            debug.log(BRAND, f"Fetch Collection {collectionName}")

            productsData = self.requestAPI(f"collection.php/{collectionID}")

            for product in productsData:
                productID = product['productID']

                productData = self.requestAPI(f"product.php/{productID}")
                row = productData[0]

                try:
                    mpn = common.toText(row['VendorItem#'])
                    sku = f"YORK {mpn}"

                    pattern = common.toText(
                        re.sub(r'\s{2,}', ' ', re.sub(r'Wallpaper|\"', '', row['ProductName'])))
                    color = common.toText(
                        re.sub(r'\"', '', re.sub(r',\s*', '/', row['Color'])))

                    # Categorization
                    brand = BRAND
                    type = "Wallpaper"
                    manufacturer = common.toText(row['CategoryName'])
                    collection = common.toText(row['CollectionName'])

                    # Main Information
                    description_parts = [common.toText(row[key].replace('"', "")) for key in [
                        'AdvertisingCopy', 'AdvertisingCopyII', 'AdvertisingCopyIII'] if row[key]]
                    description = ' '.join(description_parts).strip()
                    width = 0

                    # Additional Information
                    yardsPR = 0
                    match = common.toText(row['Match'])
                    usage = "Wallcovering"
                    country = common.toText(row['CountryOfOrigin'])
                    upc = common.toText(row['UPC'])

                    dimension = common.toText(row['ProductDimension'])

                    if "x" in dimension:
                        width = common.toFloat(dimension.split("x")[0])
                        yardsPR = common.toFloat(dimension.split("x")[1])

                    repeat = common.toText(row['PatternRepeat'])

                    specs = [
                        ("Dimension", dimension),
                        ("Repeat", repeat),
                    ]
                    features = [common.toText(row['KeyFeatures'])]

                    # Measurement
                    uom = common.toText(row['UOM']).title()
                    minimum = common.toInt(row['OrderIncrement'])
                    increment = minimum

                    # Pricing
                    cost = common.toFloat(row['DECBESTPRICE'])
                    msrp = common.toFloat(row['MSRP'])
                    map = common.toFloat(row['NewMap'])

                    # Tagging
                    keywords = f"{collection} {pattern} {description} {row['Substrate']} {row['Theme']}"
                    colors = color

                    # Status determination
                    statusP = row['SKUStatus'] in ("Active", "Retired")
                    statusS = row['SKUStatus'] in ("Active")
                    outlet = row['SKUStatus'] in ("Retired")
                    quickShip = row['QuickShip'] == 'Y'

                    # Fine-tuning
                    MANUFACTURER_DICT = {
                        "Ron Redding Designs": "Ronald Redding Designs",
                        "Ronald Redding": "Ronald Redding Designs",
                        "Cary Lind Designs": "Carey Lind Designs",
                        "Rifle": "Rifle Paper Co.",
                        "Lemieux et Cie": "RoomMates",
                        "CatCoq": "RoomMates",
                        "Jane Dixon": "RoomMates",
                        "Rose Lindo": "RoomMates",
                        "Nikki Chu": "RoomMates",
                        "Roommates": "RoomMates",
                    }
                    manufacturer = MANUFACTURER_DICT.get(
                        manufacturer, manufacturer)

                    UOM_DICT = {
                        "Single Roll": "Roll"
                    }
                    uom = UOM_DICT.get(uom, uom)

                    if "Mural" in pattern:
                        pattern = pattern.replace("Mural", "").strip()
                        type = "Mural"

                    statusS = False
                    name = f"{pattern} {color} {type}"

                    # Exceptions
                    if cost == 0 or not pattern or not color or not type or not uom:
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

                    'yardsPR': yardsPR,
                    'match': match,
                    'usage': usage,
                    'features': features,
                    'specs': specs,
                    'usage': usage,
                    'country': country,
                    'upc': upc,

                    'uom': uom,
                    'minimum': minimum,
                    'increment': increment,

                    'cost': cost,
                    'msrp': msrp,
                    'map': map,

                    'keywords': keywords,
                    'colors': colors,

                    'statusP': statusP,
                    'statusS': statusS,
                    'outlet': outlet,
                    'quickShip': quickShip,
                }
                products.append(product)

        return products

    def image(self, fullSync=False):
        hasImageIds = Product.objects.filter(manufacturer__brand=BRAND).filter(
            images__position=1).values_list('shopifyId', flat=True).distinct()

        feeds = York.objects.exclude(productId=None)
        if not fullSync:
            feeds = feeds.exclude(productId__in=hasImageIds)

        # Get Image Paths in SFTP
        productIds = []
        thumbnailArray = {}
        roomsetsArray = {}

        for folder in common.browseSFTP(brand=BRAND, src=f"/york/"):
            print(f"Retrieving images in {folder} folder.")

            for image in common.browseSFTP(brand=BRAND, src=f"/york/{folder}"):
                if "_" in image:
                    try:
                        feed = feeds.get(mpn=image.split("_")[0])
                        productIds.append(feed.productId)

                        if feed.productId not in roomsetsArray:
                            roomsetsArray[feed.productId] = []
                        roomsetsArray[feed.productId].append(
                            f"/york/{folder}/{image}")
                    except York.DoesNotExist:
                        continue
                else:
                    try:
                        feed = feeds.get(mpn=image.split(".")[0])
                        productIds.append(feed.productId)

                        thumbnailArray[feed.productId] = f"/york/{folder}/{image}"
                    except York.DoesNotExist:
                        continue

        # Download Images
        for productId in list(set(productIds)):
            thumbnail = thumbnailArray.get(productId, None)
            roomsets = roomsetsArray.get(productId, [])

            if thumbnail:
                common.downloadFileFromSFTP(
                    brand=BRAND, src=thumbnail, dst=f"{IMAGEDIR}/thumbnail/{productId}.jpg")

            for index, roomset in enumerate(roomsets):
                common.downloadFileFromSFTP(
                    brand=BRAND, src=roomset, dst=f"{IMAGEDIR}/roomset/{productId}_{index + 2}.jpg")

    def inventory(self):
        stocks = []

        products = York.objects.filter(statusP=True)
        for product in products:
            mpn = product.mpn
            sku = product.sku

            try:
                data = self.requestAPI(f"stock.php/{mpn}")

                stockP = common.toInt(data[0]["amount"])

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
