from django.core.management.base import BaseCommand
from django.db.models import Q

from tqdm import tqdm
import xml.dom.minidom as MD
import xml.etree.ElementTree as ET
import re
import environ
import os

from utils import debug, common
from vendor.models import Product, Roomvo

env = environ.Env()

PROCESS = "Roomvo"


class Command(BaseCommand):
    help = f"Run {PROCESS}"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        with Processor() as processor:
            processor.roomvo()


class Processor:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def roomvo(self):

        Roomvo.objects.all().delete()

        products = Product.objects.all()

        # High resolution images
        products = products.filter(images__hires=True)

        # Specific types only
        products = products.filter(type__name__in=[
            "Wallpaper",
            "Mural",
            "Rug",
            "Mirror"
            "Wall Art",
            "Wall Mirror",
            "Wall Hanging",
            "Wall Accent",
        ])

        # Generate Roomvo Feed
        for product in products:

            # Category
            brand = product.manufacturer.brand

            type = product.type.name if product.type.parent == "Root" else product.type.parent
            TYPE_DICT = {
                "Rug": "Area Rug",
                "Mirror": "Wall Art",
            }
            type = TYPE_DICT.get(type, type)

            # Dimensions
            width = product.width
            width = f"{width} in" if width > 0 else ""

            length = product.length or product.yardsPR * 36
            length = f"{length} in" if length > 0 else ""

            height = product.height
            height = f"{height} in" if height > 0 else ""

            if not width or not length:
                continue

            sizeDisplay = product.size if product.size else ""
            if type == "Wallpaper" and product.yardsPR > 0:
                sizeDisplay = f"{width} x {product.yardsPR} yds"

            repeatH = f"{product.repeatH} in" if product.repeatH > 0 else ""
            repeatV = f"{product.repeatV} in" if product.repeatV > 0 else ""

            layout = "Repeat" if repeatH or repeatV else None
            match = product.match
            layout = ", ".join(filter(None, [layout, match])) or ""

            # Tagging
            categories = ", ".join(product.tags.filter(
                type="Category").values_list('name', flat=True))
            styles = ", ".join(product.tags.filter(
                type="Style").values_list('name', flat=True))
            colors = ", ".join(product.tags.filter(
                type="Color").values_list('name', flat=True))

            subtype = "" if product.type.parent == "Root" else product.type.name

            # Image
            images = product.images.filter(hires=True)
            if len(images) == 0:
                continue

            Roomvo.objects.create(
                sku=product.sku,
                name=product.title,

                width=width,
                length=length,
                thickness=height,

                dimension_display=sizeDisplay,
                horizontal_repeat=repeatH,
                vertical_repeat=repeatV,
                layout=layout,

                brand=brand,
                product_type=type,

                filter_category=categories,
                filter_style=styles,
                filter_color=colors,
                filter_subtype=subtype,

                link=f'https://www.decoratorsbest.com/products/{product.shopifyHandle}',
                image=images[0].url,

                cart_id=product.consumerId,
                cart_id_trade=product.tradeId,
                cart_id_sample=product.sampleId,
                cart_id_free_sample=product.freeSampleId,
            )

            debug.log(
                PROCESS, f"Roomvo Feed for {product.sku} has been created successfully")
