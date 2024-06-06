from django.core.management.base import BaseCommand

import os
import environ
from tqdm import tqdm
import pysftp
import paramiko

from utils import common, const, debug

from vendor.models import Product, Inventory

env = environ.Env()

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"


class Command(BaseCommand):
    help = f"Generate feed for Feedonomics"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        processor = Processor()
        processor.feedonomics()


class SFTP(pysftp.Connection):
    def __init__(self, *args, **kwargs):
        try:
            if kwargs.get('cnopts') is None:
                kwargs['cnopts'] = pysftp.CnOpts()
        except pysftp.HostKeysException as e:
            self._init_error = True
            raise paramiko.ssh_exception.SSHException(str(e))
        else:
            self._init_error = False

        self._sftp_live = False
        self._transport = None
        super().__init__(*args, **kwargs)

    def __del__(self):
        if not self._init_error:
            self.close()


class Processor:
    def __init__(self):
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        self.sftp = SFTP(
            host=const.sftp["Feedonomics"]["host"],
            port=const.sftp["Feedonomics"]["port"],
            username=const.sftp["Feedonomics"]["user"],
            password=const.sftp["Feedonomics"]["pass"],
            cnopts=cnopts
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def feedonomics(self):

        header = [
            'MPN',
            'SKU',
            'URL',
            'Title',
            'Pattern',
            'Color',
            'Manufacturer',
            'Type',
            'Collection',
            'Description',
            'Width',
            'Length',
            'Height',
            'Size',
            'Vertical Repeat',
            'Horizontal Repeat',
            'Additional Specs',
            'UOM',
            'Minimum Quantity',
            'Order Increment',
            'Yards Per Roll',
            'Content',
            'Match',
            'Material',
            'Finish',
            'Care',
            'Country',
            'Features',
            'Usage',
            'Disclaimer',
            'Tags',
            'Cost',
            'Price',
            'Weight',
            'GTIN',
            'Image',
        ]

        rows = []

        products = Product.objects.filter(published=True).filter(
            images__position=1).exclude(type="Trim")

        for product in tqdm(products):
            manufacturer = "DB By DecoratorsBest" if product.manufacturer.brand in [
                "Premier Prints",
                "Materialworks",
                "Tempaper"
            ] else product.manufacturer.name
            image = product.images.filter(position=1).first().url
            tags = set(product.tags.values_list('name', flat=True).distinct())

            try:
                specs = ', '.join(
                    [f"{key}: {value}" for key, value in product.specs])
            except:
                specs = ""

            if not image:
                continue

            if product.manufacturer.brand == "Surya" and product.collection in const.NON_MAP_SURYA:
                continue

            if product.manufacturer.brand == "Brewster" and "Peel & Stick" in product.title:
                continue

            try:
                inventory = Inventory.objects.get(sku=product.sku)
                if inventory.quantity < product.minimum:
                    continue
            except Inventory.DoesNotExist:
                continue

            row = [
                product.mpn,
                product.sku,
                f"https://www.decoratorsbest.com/products/{product.shopifyHandle}",
                product.title,
                product.pattern,
                product.color,
                manufacturer,
                product.type.name,
                product.collection,
                product.description,
                product.width,
                product.length,
                product.height,
                product.size,
                product.repeatV,
                product.repeatH,
                specs,
                product.uom,
                product.minimum,
                product.increment,
                product.yardsPR,
                product.content,
                product.match,
                product.material,
                product.finish,
                product.care,
                product.country,
                ", ".join(product.features),
                product.usage,
                product.disclaimer,
                ", ".join(tags),
                product.cost,
                product.consumer,
                product.weight,
                product.upc,
                image,
            ]

            rows.append(row)

        common.writeDatasheet(
            filePath=f"{FILEDIR}/decoratorsbest-feedonomics-feed.xlsx",
            header=header,
            rows=rows
        )

        self.upload()

    def upload(self):
        try:
            with self.sftp.cd('/incoming'):
                self.sftp.put(
                    f"{FILEDIR}/decoratorsbest-feedonomics-feed.xlsx")

        except Exception as e:
            debug.error(
                "Feedonomics", f"Uploading Feedonomics feed failed. {str(e)}")
