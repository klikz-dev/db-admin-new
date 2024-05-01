from django.core.management.base import BaseCommand

import os
import glob
from PIL import Image as PILImage

from utils import debug, aws, shopify, common
from vendor.models import Product, Image

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

PROCESS = "Sync-Image"


class Command(BaseCommand):
    help = f"Run {PROCESS}"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        with Processor() as processor:
            for path in ["thumbnail", "roomset", "hires"]:
                processor.compress(path)

            processor.upload()


class Processor:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def compress(self, path):

        files = glob.glob(f"{FILEDIR}/images/{path}/*.*")
        total = len(files)

        def getSize(img):
            MAX_WIDTH = 2048

            width, height = img.size

            if MAX_WIDTH < width:
                ratio = width / height
                return (MAX_WIDTH, int(MAX_WIDTH / ratio))
            else:
                return (width, height)

        def compressFile(index, file):
            fpath, ext = os.path.splitext(file)
            fname = os.path.basename(fpath)

            with PILImage.open(file) as img:
                if ext.lower() == ".jpg":
                    compressed = img.convert("RGB").resize(
                        getSize(img), PILImage.LANCZOS)
                    compressed.save(
                        f"{FILEDIR}/images/compressed/{fname}.jpg", "JPEG")

                elif ext.lower() == ".png":
                    compressed = img.resize(
                        getSize(img), PILImage.LANCZOS)
                    compressed.save(
                        f"{FILEDIR}/images/compressed/{fname}.png", "PNG")

                else:
                    debug.warn(PROCESS, f"Unknow Image Type: {file}")
                    return

            os.remove(file)
            debug.log(
                PROCESS, f"{index}/{total}: Successfully compressed {file}")

        common.thread(rows=files, function=compressFile)

    def upload(self):
        awsManager = aws.AWSManager()

        images = glob.glob(f"{FILEDIR}/images/compressed/*.*")
        total = len(images)

        def uploadImage(index, image):

            shopifyManager = shopify.ShopifyManager(thread=index)

            fpath, ext = os.path.splitext(image)
            fname = os.path.basename(fpath)

            if "_" in fname:
                productId = fname.split("_")[0]
                position = fname.split("_")[1]
                if "hires" in position:
                    hires = True
                    position = 1
                    fname = fname.replace("_hires", "")
                else:
                    hires = False

            else:
                productId = fname
                position = 1
                hires = False

            try:
                product = Product.objects.get(shopifyId=productId)
            except Product.DoesNotExist:
                return

            if ext == ".jpg":
                contentType = 'image/jpeg'
            elif ext == ".png":
                contentType = 'image/png'
            else:
                debug.warn(PROCESS, f"Unknow Image Type: {image}")
                return

            # Upload Image to AWS
            imageLink = awsManager.uploadImage(
                src=image, dst=f"{fname}{ext}", contentType=contentType)

            # Delete Existing Image
            try:
                currentImage = product.images.get(position=position)
                shopifyManager.deleteImage(
                    productId=product.shopifyId, imageId=currentImage.shopifyId)
                currentImage.delete()
            except Image.DoesNotExist:
                pass

            # Upload Image to Shopify
            imageData = shopifyManager.uploadImage(
                productId=productId, position=position, link=imageLink, alt=product.title)

            Image.objects.create(
                shopifyId=imageData['id'],
                url=imageData['src'],
                position=position,
                product=product,
                hires=hires
            )

            os.remove(image)

            debug.log(
                PROCESS, f"{index}/{total}: Image {image} has been uploaded successfully")

        common.thread(rows=images, function=uploadImage)
