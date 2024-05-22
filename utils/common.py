from concurrent.futures import ThreadPoolExecutor, as_completed

import os
from shutil import copyfile
import smtplib
import environ
import urllib
import paramiko
import math
import re
import inflect
import pycountry
import xlsxwriter

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from utils import debug, const, shopify
from vendor.models import Product

env = environ.Env()
p = inflect.engine()

PROCESS = "Common"


def thread(rows, function):
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_row = {executor.submit(
            function, index, row): row for index, row in enumerate(rows)}

        for future in as_completed(future_to_row):
            try:
                future.result()
            except Exception as e:
                debug.warn(PROCESS, f"{str(e)}")


def sendEmail(sender, recipient, subject, body):
    message = MIMEMultipart()
    message["From"] = sender
    message["Subject"] = subject
    html = MIMEText(body, "html")
    message.attach(html)

    smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    smtp.ehlo()
    smtp.login(env('EMAIL_USER'), env('EMAIL_PASS'))

    if isinstance(recipient, list):
        for receiver in recipient:
            message["To"] = receiver
            smtp.sendmail(sender, receiver, message.as_string())

    else:
        message["To"] = recipient
        smtp.sendmail(sender, recipient, message.as_string())

    smtp.close()


def browseSFTP(brand, src=""):
    host = const.sftp[brand]["host"]
    port = const.sftp[brand]["port"]
    username = const.sftp[brand]["user"]
    password = const.sftp[brand]["pass"]

    try:
        transport = paramiko.Transport((host, port))
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)
    except Exception as e:
        debug.warn(brand, f"Connect to {brand} SFTP Server. {str(e)}")
        return []

    if src != "":
        sftp.chdir(src)

    files = sftp.listdir()

    sftp.close()

    return files


def downloadFileFromSFTP(brand, src, dst, fileSrc=True, delete=False):
    host = const.sftp[brand]["host"]
    port = const.sftp[brand]["port"]
    username = const.sftp[brand]["user"]
    password = const.sftp[brand]["pass"]

    if host == "decoratorsbestam.com" and not delete:
        src = f"/var/sftp/{username}{src}"

        if fileSrc:
            copyfile(src, dst)
            if delete:
                os.remove(src)
        else:
            files = os.listdir(src)
            for file in files:
                copyfile(f"{src}/{file}", dst)
                if delete:
                    os.remove(f"{src}/{file}")

        debug.log(brand, f"Download Local SFTP file From {src} To {dst}")

    else:
        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
        except Exception as e:
            debug.warn(brand, f"Connect to {brand} SFTP Server. {str(e)}")
            return

        if fileSrc:
            try:
                sftp.stat(src)
                sftp.get(src, dst)
                debug.log(brand, f"Download SFTP file From {src} To {dst}")

                if delete:
                    sftp.remove(src)
            except Exception as e:
                debug.warn(
                    brand, f"Download SFTP file From {src} To {dst}. {str(e)}")
        else:
            try:
                if src != "":
                    sftp.chdir(src)

                files = sftp.listdir()
                for file in files:
                    if "EDI" in file:
                        continue

                    sftp.stat(file)
                    sftp.get(file, dst)
                    debug.log(brand, f"Download SFTP file From {src} To {dst}")

                    if delete:
                        sftp.remove(file)
            except Exception as e:
                debug.warn(
                    brand, f"Download SFTP file From {src} To {dst}. {str(e)}")
                return

        sftp.close()


def downloadFileFromFTP(brand, src, dst):
    host = const.ftp[brand]["host"]
    username = const.ftp[brand]["user"]
    password = const.ftp[brand]["pass"]

    try:
        urllib.request.urlretrieve(
            f"ftp://{username}:{password}@{host}/{src}", dst)
        debug.log(brand, f"Download FTP file From {src} To {dst}")
    except Exception as e:
        debug.warn(brand, f"Download FTP file From {src} To {dst}. {str(e)}")


def downloadFileFromLink(src, dst):
    try:
        urllib.request.urlretrieve(src, dst)
        debug.log(PROCESS, f"Download From {src} To {dst}")
    except Exception as e:
        debug.warn(PROCESS, f"Download From {src} To {dst}. Error: {str(e)}")


def toText(text):
    if text:
        text = re.sub(r'[^\x20-\x7E]+', '', str(text))
        return text.replace("N/A", "").replace("n/a", "").strip()
    else:
        return ""


def toFloat(value):
    if value:
        try:
            value = round(float(str(value).lower().replace("n/a", "").replace('"', "").replace("'", "").replace("in", "").replace(
                ",", "").replace("kg", "").replace('$', "").replace("s/r", "").replace("bolt", "").replace("yds", "").replace("yd", "").replace("/", "")), 2)
        except:
            value = 0
    else:
        value = 0

    if value == int(value):
        return int(value)
    else:
        return value


def toInt(value):
    return int(toFloat(value))


def toHandle(text):
    if text:
        handle = str(text).lower().replace(" ", "-")
        handle = re.sub(r'[^a-z0-9-]', '', handle)
        handle = re.sub(r'-+', '-', handle)

        return handle.strip('-')
    else:
        return ""


def pluralToSingular(word):
    singular = p.singular_noun(word)
    return singular if singular else word


def getRelatedProducts(product):
    samePatterns = Product.objects.filter(
        manufacturer=product.manufacturer, type=product.type, collection=product.collection, pattern=product.pattern)

    relatedProducts = []
    for samePattern in samePatterns:
        color = samePattern.color
        size = samePattern.size
        handle = toHandle(samePattern.title)

        relatedProducts.append({
            "color": color,
            "size": size,
            "handle": handle
        })

    return relatedProducts


def wordInText(word, text):
    if str(word) and str(text):
        pattern = r'\b' + re.escape(str(word)) + r'\b'
        return re.search(pattern, str(text), re.IGNORECASE) is not None
    else:
        return False


def getPricing(feed):
    def toPrice(value, markup):
        price = math.ceil(value * markup * 4) / 4
        if price == int(price):
            price -= 0.01
        return price

    markup = const.markup[feed.brand]

    if feed.type in markup:
        markup = markup[feed.type]
    if feed.european and "European" in markup:
        markup = markup["European"]

    cost = feed.cost
    map = feed.map
    consumer = toPrice(cost, markup['consumer'])
    trade = toPrice(cost, markup['trade'])

    consumer = map if map > 0 else consumer

    if consumer < 20:
        consumer = 19.99
    if trade < 17:
        trade = 16.99

    sample = 5 if feed.type in [
        "Wallpaper",
        "Mural",
        "Fabric",
        "Trim",
        "Pillow",
        "Pillow Kit",
        "Pillow Cover",
        "Outdoor Pillow",
        "Decorative Pillow"
    ] else 15
    compare = None

    return (consumer, trade, sample, compare)


def provinceCode(province):
    try:
        subdivisions = list(pycountry.subdivisions.get(country_code="US"))
        for subdivision in subdivisions:
            if subdivision.name.lower() == province.lower():
                return subdivision.code.split('-')[-1]
        return province
    except LookupError:
        return province


def addTracking(order, brand, number, company):
    shopifyManger = shopify.ShopifyManager()

    # all brand variants in order
    variants = []

    for lineItem in order.lineItems.filter(product__manufacturer__brand=brand):
        if lineItem.variant == "Trade":
            variantId = lineItem.product.tradeId
        elif lineItem.variant == "Sample":
            variantId = lineItem.product.sampleId
        elif lineItem.variant == "Free Sample":
            variantId = lineItem.product.freeSampleId
        else:
            variantId = lineItem.product.consumerId

        variants.append(variantId)
    # all brand variants in order

    # list of line items to fulfill
    fulfillmentOrder = shopifyManger.getFulfillment(
        orderId=order.shopifyId)

    if not fulfillmentOrder:
        debug.log(
            PROCESS, f"#{order} doesn't have any items to fulfill")
        return

    itemsToFulfill = []
    for lineItem in fulfillmentOrder['line_items']:
        if str(lineItem['variant_id']) in variants:
            if lineItem['fulfillable_quantity'] == 0:
                continue

            itemsToFulfill.append({
                'id': lineItem['id'],
                'quantity': lineItem['fulfillable_quantity']
            })

    if len(itemsToFulfill) == 0:
        debug.log(
            PROCESS, f"#{order} doesn't have any {brand} items to fulfill")
        return
    # list of line items to fulfill

    # Upload tracking to Shopify
    fulfillmentData = {
        "fulfillment": {
            "location_id": '14712864835',
            "tracking_info": {
                "number": number,
                "company": company or "UPS",
            },
            "line_items_by_fulfillment_order": [{
                "fulfillment_order_id": fulfillmentOrder['id'],
                "fulfillment_order_line_items": itemsToFulfill
            }]
        }
    }

    fulfillmentData = shopifyManger.createFulfillment(payload=fulfillmentData)

    if "fulfillment" in fulfillmentData:
        debug.log(
            PROCESS, f"#{order} {brand} Tracking Uploaded. {company}:{number}")
    # Upload tracking to Shopify


def writeDatasheet(filePath, header, rows):
    workbook = xlsxwriter.Workbook(filePath)
    worksheet = workbook.add_worksheet()

    worksheet.write_row(0, 0, header)

    for rowId, row in enumerate(rows):
        for columnId, column in enumerate(row):
            worksheet.write(rowId + 1, columnId, column)

    workbook.close()
