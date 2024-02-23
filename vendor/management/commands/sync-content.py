import requests
import json

from django.core.management.base import BaseCommand

from utils import debug, common, shopify
from vendor.models import Product, Sync


class Command(BaseCommand):
    help = f"Sync Content"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()

        if "content" in options['functions']:
            processor.content()


class Processor:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def content(self):
        productIds = Sync.objects.filter(type="Content")
        for productId in productIds:
            try:
                product = Product.objects.get(shopifyId=productId)
            except Product.DoesNotExist:
                debug.warn("Sync Content", f"{productId} Not Found")
                continue

            try:
                handle = shopify.updateProduct(product)
            except Exception as e:
                debug.warn("Sync Content",
                           f"{productId} Update Error: {str(e)}")
                continue

            product.shopifyHandle = handle
            product.save()

            debug.log("Sync Content",
                      f"Product {productId} has been updated successfully")
