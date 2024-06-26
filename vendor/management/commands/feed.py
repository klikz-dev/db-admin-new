from django.core.management.base import BaseCommand

from tqdm import tqdm
import xml.dom.minidom as MD
import xml.etree.ElementTree as ET
import re
import environ
import os

from utils import debug, common, aws
from vendor.models import Product, Inventory

env = environ.Env()

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"
FEED_DIR = f"{FILEDIR}/feed/DecoratorsBestFeed.xml"
FEED_ERROR_DIR = f"{FILEDIR}/feed/DecoratorsBestFeed_error.xml"

PROCESS = "Feed"

nonMAPSurya = [
    "Alamo",
    "Alanya",
    "Alfombra",
    "Alhambra",
    "Alice",
    "Aliyah Shag",
    "Amelie",
    "Amore",
    "Anika",
    "Ankara",
    "Antiquity",
    "Aranya",
    "Atlanta",
    "Barbados",
    "Basel",
    "Beni Shag",
    "Big Sur",
    "Birmingham",
    "Bitlis",
    "Bodrum",
    "Cabo",
    "Calhoun",
    "California Shag",
    "Calla",
    "Cesar",
    "Chelsea",
    "Chester",
    "City",
    "City Light",
    "Cloudy Shag",
    "Cobb",
    "Colin",
    "Davaro",
    "Davina",
    "Delphi",
    "Deluxe Shag",
    "Dublin",
    "Eagean",
    "Elaziz",
    "Elenor",
    "Elle",
    "Elysian Shag",
    "Enfield",
    "Farrell",
    "Firenze",
    "Floransa",
    "Fluffy Shag",
    "Freud",
    "Hampton",
    "Harput",
    "Hera",
    "Huntington Beach",
    "Iris",
    "Jefferson",
    "Jolie",
    "Katmandu",
    "Kayra",
    "Kemer",
    "Kimi",
    "La Casa",
    "Lavadora",
    "Leicester",
    "Lila",
    "Lillian",
    "Long Beach",
    "Luca",
    "Lustro",
    "Lykke",
    "Lyra Shag",
    "Margaret",
    "Margot",
    "Marlene",
    "Marvel",
    "Maryland Shag",
    "Merino",
    "Moda shag",
    "Monaco",
    "Monte Carlo",
    "Mood",
    "Morocco",
    "Morocotton",
    "Murat",
    "Murcia",
    "New Mexico",
    "Nomadic",
    "Olivia",
    "Paramount",
    "Pasadena",
    "Perception",
    "Pertek",
    "Pisa",
    "Pismo Beach",
    "Positano",
    "Rafetus",
    "Ravello",
    "Redondo Beach",
    "Riley",
    "Rivi",
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


class Command(BaseCommand):
    help = f"Run {PROCESS}"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        with Processor() as processor:
            processor.feed()


class Processor:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def feed(self):

        if os.path.isfile(FEED_DIR):
            os.remove(FEED_DIR)
        if os.path.isfile(FEED_ERROR_DIR):
            os.remove(FEED_ERROR_DIR)

        products = Product.objects.filter(published=True).exclude(
            type="Trim").exclude(manufacturer__brand="Poppy")

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

            type = product.type.name if product.type.parent == "Root" else product.type.parent

            pattern = product.pattern
            description = product.description or product.title
            weight = product.weight
            upc = product.upc

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
            upc = upc if re.match(r'^\d{11,14}$', upc) else ""

            privateBrands = [
                "Covington",
                "Premier Prints",
                "Materialworks",
                "Tempaper"
            ]
            if brand in privateBrands:
                manufacturer = "DB By DecoratorsBest"

            if (type == "Wallpaper" or type == "Fabric" or type == "Pillow") and type not in manufacturer:
                manufacturer = f"{manufacturer} {type}"

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

            if brand == "Brewster":
                sku = sku.replace("BREWSTER", "Brewster")
                sku = sku.replace("STREET", "Street")
                if "Peel & Stick" in title:
                    debug.log(
                        PROCESS, f"IGNORED SKU {sku}. Brewster Peel & Stick")
                    skipped += 1
                    continue

            if bool(re.search(r'\bget\b', f"{title}, {description}", re.IGNORECASE)):
                debug.log(
                    PROCESS, f"IGNORED SKU {sku}. 'Get' word in the description")
                skipped += 1
                continue

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
            ET.SubElement(item, "g:gtin").text = f"{upc}"
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

        self.google()
        self.facebook()

    def google(self):
        awsManager = aws.AWSManager()

        feed = awsManager.uploadFeed(src=FEED_DIR, dst="DecoratorsBestGS.xml")
        debug.log(PROCESS, f"Uploaded to {feed}")

    def facebook(self):
        awsManager = aws.AWSManager()

        feed = awsManager.uploadFeed(src=FEED_DIR, dst="DecoratorsBestFB.xml")
        debug.log(PROCESS, f"Uploaded to {feed}")
