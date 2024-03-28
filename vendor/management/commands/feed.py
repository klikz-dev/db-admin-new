from django.core.management.base import BaseCommand

import os
import environ
import re
import boto3
import xml.etree.ElementTree as ET
import xml.dom.minidom as MD
from tqdm import tqdm

from utils import debug, common

from vendor.models import Product, Inventory

env = environ.Env()


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"
FEED_DIR = f"{FILEDIR}/feed/DecoratorsBestGS.xml"
FEED_ERROR_DIR = f"{FILEDIR}/feed/DecoratorsBestGS_error.xml"

PROCESS = "Feed"


class Command(BaseCommand):
    help = f"Run {PROCESS} processor"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "main" in options['functions']:
            with Processor() as processor:
                processor.feed()


class Processor:
    def __init__(self):
        self.bucket = 'decoratorsbestimages'

    def __enter__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=env('AWS_ACCESS'),
            aws_secret_access_key=env('AWS_SECRET')
        )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def feed(self):

        if os.path.isfile(FEED_DIR):
            os.remove(FEED_DIR)
        if os.path.isfile(FEED_ERROR_DIR):
            os.remove(FEED_ERROR_DIR)

        products = Product.objects.filter(published=True).exclude(type="Trim")

        root = ET.Element("rss")
        root.set("xmlns:g", "http://base.google.com/ns/1.0")

        channel = ET.SubElement(root, "channel")

        title = ET.SubElement(channel, "title")
        title.text = "DecoratorsBest"

        link = ET.SubElement(channel, "link")
        link.text = "https://www.decoratorsbest.com/"

        description = ET.SubElement(channel, "description")
        description.text = "DecoratorsBest"

        total = len(products)
        skipped = 0
        for product in tqdm(products):
            mpn = product.mpn
            sku = product.sku
            title = f"{product.title} - {sku}"

            shopifyId = product.shopifyId
            shopifyHandle = product.shopifyHandle

            brand = product.manufacturer.brand
            manufacturer = product.manufacturer.name
            type = product.type

            pattern = product.pattern
            description = product.description or product.title
            weight = product.weight
            barcode = product.barcode

            cost = product.cost
            consumer = product.consumer
            minimum = product.minimum or 1
            price = consumer * minimum

            images = product.images.filter(position=1).values_list(
                'url', flat=True).distinct()
            imageURL = images[0] if len(images) > 0 else None

            styles = product.tags.filter(type="Category").values_list(
                'name', flat=True).distinct()
            style = styles[0] if len(styles) > 0 else pattern

            colors = product.tags.filter(type="Color").values_list(
                'name', flat=True).distinct()
            color = colors[0] if len(colors) > 0 else product.color

            # Fine Tuning
            barcode = barcode if re.match(r'^\d{11,14}$', barcode) else ""

            privateBrands = [
                "Covington",
                "Premier Prints",
                "Materialworks",
                "Tempaper"
            ]
            if brand in privateBrands:
                manufacturer = "DB By DecoratorsBest"

            price_thresholds = [
                (300, "300+"),
                (250, "250-300"),
                (200, "200-250"),
                (150, "150-200"),
                (100, "100-150"),
                (50, "50-100"),
                (25, "25-50"),
                (10, "10-25")
            ]
            priceRange = None

            for threshold, label in price_thresholds:
                if price > threshold:
                    priceRange = label
                    break

            margin = common.toInt((consumer - cost) / cost * 100)

            if type == "Fabric":
                productCategory = "Arts & Entertainment > Hobbies & Creative Arts > Arts & Crafts > Art & Crafting Materials > Textiles > Fabric"
                productType = "Home & Garden > Bed and Living Room > Home Fabric"
            elif type == "Wallpaper":
                productCategory = "Home & Garden > Decor > Wallpaper"
                productType = "Home & Garden > Bed and Living Room > Home Wallpaper"
            elif type == "Pillow":
                productCategory = "Home & Garden > Decor > Throw Pillows"
                productType = "Home & Garden > Bed and Living Room > Home Pillow"
            elif type == "Trim":
                productCategory = "Arts & Entertainment > Hobbies & Creative Arts > Arts & Crafts > Art & Crafting Materials > Embellishments & Trims"
                productType = "Home & Garden > Bed and Living Room > Home Trim"
            elif type == "Furniture":
                productCategory = "Furniture"
                productType = "Home & Garden > Bed and Living Room > Home Furniture"
            else:
                productCategory = "Home & Garden > Decor"
                productType = "Home & Garden > Decor"

            material = product.material

            # Exceptions
            if not imageURL:
                debug.log(PROCESS, f"IGNORED SKU {sku}. No Image")
                skipped += 1
                continue

            if brand == "Brewster" and "Peel & Stick" in title:
                debug.log(
                    PROCESS, f"IGNORED SKU {sku}. Brewster Peel & Stick")
                skipped += 1
                continue

            if bool(re.search(r'\bget\b', f"{title}, {description}", re.IGNORECASE)):
                debug.log(
                    PROCESS, f"IGNORED SKU {sku}. 'Get' word in the description")
                skipped += 1
                continue

            nonMAPSurya = [
                "Rodos",
                "Roma",
                "San Diego",
                "Santana",
                "Serapi",
                "Skagen",
                "Solana",
                "Soldado",
                "St Tropez",
                "Sunderland",
                "Tahmis",
                "Taza Shag",
                "Tevazu",
                "Tuareg",
                "Ustad",
                "Venezia",
                "Veranda",
                "Wanderlust",
                "West Palm",
                "Zidane",
            ]
            if brand == "Surya" and product.collection in nonMAPSurya:
                debug.log(PROCESS, f"IGNORED SKU {sku}. Non MAP Surya")
                skipped += 1
                continue

            if priceRange is None:
                debug.log(PROCESS, f"IGNORED SKU {sku}. Price issue")
                skipped += 1
                continue

            # Inventory
            try:
                inventory = Inventory.objects.get(sku=sku, brand=brand)

                if inventory.quantity < minimum:
                    debug.log(
                        PROCESS, f"IGNORED SKU {sku}. Inventory insufficient")
                    skipped += 1
                    continue

            except Inventory.DoesNotExist:
                debug.log(
                    PROCESS, f"IGNORED SKU {sku}. Inventory not found")
                skipped += 1
                continue

            # Write Row
            item = ET.SubElement(channel, "item")

            ET.SubElement(item, "g:id").text = f"{sku}"
            ET.SubElement(item, "g:item_group_id").text = f"{shopifyId}"
            ET.SubElement(item, "g:title").text = f"{title}"
            ET.SubElement(item, "g:description").text = f"{description}"
            ET.SubElement(
                item, "g:google_product_category").text = f"{productCategory}"
            ET.SubElement(
                item, "g:link").text = f"https://www.decoratorsbest.com/products/{shopifyHandle}"
            ET.SubElement(item, "g:image_link").text = f"{imageURL}"
            ET.SubElement(item, "g:availability").text = "in stock"
            ET.SubElement(
                item, "g:quantity_to_sell_on_facebook").text = f"{inventory.quantity}"
            ET.SubElement(item, "g:gtin").text = f"{barcode}"
            ET.SubElement(item, "g:price").text = f"{price}"
            ET.SubElement(item, "g:brand").text = f"{manufacturer}"
            ET.SubElement(item, "g:mpn").text = f"{mpn}"
            ET.SubElement(item, "g:product_type").text = f"{productType}"
            ET.SubElement(item, "g:condition").text = "new"
            ET.SubElement(item, "g:color").text = f"{color}"
            ET.SubElement(item, "g:pattern").text = f"{style}"
            ET.SubElement(item, "g:shipping_weight").text = f"{weight}"
            ET.SubElement(item, "g:material").text = f"{material}"
            ET.SubElement(item, "g:custom_label_0").text = f"{type}"
            ET.SubElement(item, "g:custom_label_1").text = f"{manufacturer}"
            ET.SubElement(item, "g:custom_label_2").text = f"{priceRange}"
            ET.SubElement(item, "g:custom_label_3").text = f"{margin}"

        debug.log(
            PROCESS, f"Completed GS Feed Generation. skipped {skipped} out of {total} SKUs")

        tree_str = ET.tostring(root, encoding='utf-8')

        try:
            tree_dom = MD.parseString(tree_str)
            pretty_tree = tree_dom.toprettyxml(indent="\t")

            with open(FEED_DIR, 'w', encoding="UTF-8") as file:
                file.write(pretty_tree)

        except Exception as e:
            print(e)
            with open(FEED_ERROR_DIR, 'wb') as file:
                file.write(tree_str)

            return

        self.google(tree_str)
        self.facebook(tree_str)

    def google(self):

        self.s3.upload_file(FEED_DIR, self.bucket, "DecoratorsBestGS.xml", ExtraArgs={
                            'ACL': 'public-read'})
        debug.log(
            PROCESS, 'Uploaded to https://decoratorsbestimages.s3.amazonaws.com/DecoratorsBestGS.xml')

    def facebook(self):

        self.s3.upload_file(FEED_DIR, self.bucket, "DecoratorsBestFB.xml", ExtraArgs={
                            'ACL': 'public-read'})
        debug.log(
            PROCESS, 'Uploaded to https://decoratorsbestimages.s3.amazonaws.com/DecoratorsBestFB.xml')
