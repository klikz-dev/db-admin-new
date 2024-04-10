from django.core.management.base import BaseCommand
from concurrent.futures import ThreadPoolExecutor, as_completed

import os
import time
import glob
from PIL import Image as PILImage

from utils import debug, aws, shopify
from vendor.models import Product, Image

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

PROCESS = "Sync-Image"


class Command(BaseCommand):
    help = f"Run {PROCESS}"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        while True:

            with Processor() as processor:
                for path in ["thumbnail", "roomset", "hires"]:
                    processor.compress(path)

                processor.upload()

            time.sleep(60)


class Processor:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def compress(self, path):
        def getSize(img):
            MAX_WIDTH = 2048

            width, height = img.size

            if MAX_WIDTH < width:
                ratio = width / height
                return (MAX_WIDTH, int(MAX_WIDTH / ratio))
            else:
                return (width, height)

        for infile in glob.glob(f"{FILEDIR}/images/{path}/*.*"):

            try:
                fpath, ext = os.path.splitext(infile)
                fname = os.path.basename(fpath)

                with PILImage.open(infile) as img:
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
                        debug.warn(PROCESS, f"Unknow Image Type: {infile}")
                        continue

                os.remove(infile)
                debug.log(PROCESS, f"Successfully compressed {infile}")

            except Exception as e:
                debug.log(
                    PROCESS, f"Failed compresssing {infile}. {str(e)}")

    def upload(self):
        awsManager = aws.AWSManager()
        shopifyManager = shopify.ShopifyManager()

        # for image in glob.glob(f"{FILEDIR}/images/compressed/*.*"):
        def uploadImage(index, image):
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
            imageLink = awsManager.uploadFile(
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

        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_image = {executor.submit(
                uploadImage, index, image): image for index, image in enumerate(glob.glob(f"{FILEDIR}/images/compressed/*.*"))}

            for future in as_completed(future_to_image):
                image = future_to_image[future]

                try:
                    future.result()
                    os.remove(image)

                    debug.log(
                        PROCESS, f"Image {image} has been uploaded successfully")

                except Exception as e:
                    debug.warn(
                        PROCESS, f"Image Upload for {image} has been failed. {str(e)}")
