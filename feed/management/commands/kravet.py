from django.core.management.base import BaseCommand
from feed.models import Kravet

import os
import csv
import codecs
import zipfile

from utils import database, debug, common
from vendor.models import Product

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"
IMAGEDIR = f"{os.path.expanduser('~')}/admin/vendor/management/files/images"

BRAND = "Kravet"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "feed" in options['functions']:
            common.downloadFileFromFTP(
                brand=BRAND,
                src="decbest.zip",
                dst=f"{FILEDIR}/kravet-master.zip"
            )
            z = zipfile.ZipFile(f"{FILEDIR}/kravet-master.zip", "r")
            z.extractall(FILEDIR)
            z.close()
            os.rename(f"{FILEDIR}/item_info.csv",
                      f"{FILEDIR}/kravet-master.csv")

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

        if "roomset" in options['functions']:
            processor = Processor()
            processor.roomset()

        if "inventory" in options['functions']:
            common.downloadFileFromFTP(
                brand=BRAND,
                src="decbest.zip",
                dst=f"{FILEDIR}/kravet-master.zip"
            )
            z = zipfile.ZipFile(f"{FILEDIR}/kravet-master.zip", "r")
            z.extractall(FILEDIR)
            z.close()
            os.rename(f"{FILEDIR}/item_info.csv",
                      f"{FILEDIR}/kravet-master.csv")

            processor = Processor()
            stocks = processor.inventory()
            processor.DatabaseManager.updateInventory(
                stocks=stocks, type=1, reset=True)


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

        f = open(f"{FILEDIR}/kravet-master.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
        for row in cr:
            try:
                # Primary Keys
                mpn = common.toText(row[0])
                sku = f"K {mpn.rstrip('.0').replace('.', '-')}"

                pattern = common.toText(row[1])
                color = common.toText(row[2])

                # Categorization
                brand = BRAND
                type = common.toText(row[17])

                manufacturer = common.toText(row[3])
                collection = common.toText(row[16])

                # Main Information
                width = common.toFloat(row[7])
                repeatV = common.toFloat(row[4])
                repeatH = common.toFloat(row[5])

                # Additional Information
                yardsPR = common.toFloat(row[37])
                content = common.toText(row[12])
                finish = common.toText(row[13])
                weight = common.toFloat(row[29])
                usage = common.toText(row[17])
                country = common.toText(row[9])
                disclaimer = common.toText(row[41])
                upc = common.toText(row[48])

                # Measurement
                uom = common.toText(row[11]).title()
                minimum = common.toInt(row[38])
                increment = common.toInt(row[39])

                # Pricing
                cost = common.toFloat(row[10])
                map = common.toFloat(row[49])

                # Tagging
                keywords = f"{collection} {pattern} {row[18]} {row[19]} {row[20]} {row[21]}"
                colors = f"{row[26]} {row[27]} {row[28]}"

                # Image
                thumbnail = common.toText(row[24] or row[25])

                # Status
                statusP = row[31] in ("Active", "Limited Stock")
                statusS = row[43] == "YES"
                outlet = row[31] == "Limited Stock"
                european = any(euCollection in collection for euCollection in {
                               "LIZZO", "ANDREW MARTIN", "BLITHFIELD", "JAGTAR", "JOSEPHINE MUNSEY", "MISSONI HOME", "PAOLO MOSCHINO"})

                # Fine-tuning
                TYPE_DICT = {
                    "WALLCOVERING": "Wallpaper",
                    "TRIM": "Trim",
                    "UPHOLSTERY": "Fabric",
                    "DRAPERY": "Fabric",
                    "MULTIPURPOSE": "Fabric"
                }
                type = TYPE_DICT.get(type, type)

                if "LIZZO" in collection:
                    manufacturer = "LIZZO"
                elif "ANDREW MARTIN" in collection:
                    manufacturer = "ANDREW MARTIN"

                MANUFACTURER_DICT = {
                    "PARKERTEX": "Lee Jofa",
                    "KRAVET DESIGN": "Kravet",
                    "KRAVET BASICS": "Kravet",
                    "KRAVET COUTURE": "Kravet",
                    "LEE JOFA MODERN": "Lee Jofa",
                    "KRAVET SMART": "Kravet",
                    "KRAVET CONTRACT": "Kravet",
                    "CLARKE AND CLARKE": "Clarke & Clarke",
                    "FIRED EARTH": "Lee Jofa",
                    "SEACLOTH": "Lee Jofa",
                }
                manufacturer = MANUFACTURER_DICT.get(
                    manufacturer, manufacturer).title()

                name = f"{pattern} {color} {type}"

                weight = round(weight / 16, 2)

                # Exceptions
                if not (mpn.endswith('.0') and mpn.count('.') == 2):
                    continue

                if cost == 0 or not pattern or not color or not type:
                    continue

                if uom == "Hide":
                    continue

                blockCollections = [
                    "CANDICE OLSON AFTER EIGHT",
                    "CANDICE OLSON COLLECTION",
                    "CANDICE OLSON MODERN NATURE 2ND EDITION",
                    "RONALD REDDING",
                    "RONALD REDDING ARTS & CRAFTS",
                    "RONALD REDDING TRAVELER",
                    "DAMASK RESOURCE LIBRARY",
                    "MISSONI HOME",
                    "MISSONI HOME 2020",
                    "MISSONI HOME 2021",
                    "MISSONI HOME 2022 INDOOR/OUTDOOR",
                    "MISSONI HOME WALLCOVERINGS 03",
                    "MISSONI HOME WALLCOVERINGS 04",
                ]
                if collection in blockCollections and type == "Wallpaper":
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

                'width': width,
                'repeatV': repeatV,
                'repeatH': repeatH,

                'yardsPR': yardsPR,
                'content': content,
                'finish': finish,
                'weight': weight,
                'usage': usage,
                'country': country,
                'disclaimer': disclaimer,
                'upc': upc,

                'uom': uom,
                'minimum': minimum,
                'increment': increment,

                'cost': cost,
                'map': map,

                'keywords': keywords,
                'colors': colors,

                'thumbnail': thumbnail,

                'statusP': statusP,
                'statusS': statusS,
                'outlet': outlet,
                'european': european,
            }
            products.append(product)

        return products

    def image(self, fullSync=False):
        hasImageIds = Product.objects.filter(manufacturer__brand=BRAND).filter(
            images__position=1).values_list('shopifyId', flat=True).distinct()

        feeds = Kravet.objects.exclude(productId=None)
        if not fullSync:
            feeds = feeds.exclude(productId__in=hasImageIds)

        for feed in feeds:
            if feed.thumbnail:
                common.downloadFileFromFTP(
                    brand=BRAND, src=feed.thumbnail, dst=f"{IMAGEDIR}/thumbnail/{feed.productId}.jpg")

    def roomset(self):

        feeds = Kravet.objects.exclude(productId=None).filter(
            collection="CANDICE OLSON CASUAL ELEGANCE")

        for feed in feeds:
            srcFile = feed.mpn.replace(".", "_").replace("_0", "_2")
            common.downloadFileFromFTP(
                brand=BRAND, src=f"/TWImgs/Lifestyle/{srcFile}.webp", dst=f"{IMAGEDIR}/roomset/{feed.productId}_2.jpg")

    def inventory(self):
        stocks = []

        f = open(f"{FILEDIR}/kravet-master.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
        for row in cr:
            mpn = common.toText(row[0])

            try:
                product = Kravet.objects.get(mpn=mpn)
            except Kravet.DoesNotExist:
                continue

            sku = product.sku
            stockP = common.toInt(row[46])
            stockNote = f"{common.toText(row[47])} days"

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': stockNote
            }
            stocks.append(stock)

        return stocks
