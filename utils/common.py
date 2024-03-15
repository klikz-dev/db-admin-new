import os
from shutil import copyfile
import smtplib
import environ
import urllib
import paramiko
import math
import re

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from utils import debug, const
from vendor.models import Product, Tag

env = environ.Env()

PROCESS = "Common"


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
        smtp.sendmail(sender, receiver, message.as_string())

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

    # if host == "decoratorsbestam.com":
    if False:
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
        debug.log(PROCESS, f"Download From {dst} To {src}")
    except Exception as e:
        debug.warn(PROCESS, f"Download From {dst} To {src}. Error: {str(e)}")


def toText(text):
    if text == int(text):
        return int(text)

    if text:
        return str(text).replace("N/A", "").replace("n/a", "").replace('', '').replace('¥', '').replace('…', '').replace('„', '').strip()
    else:
        return ""


def toFloat(value):
    if value and str(value).strip() != '':
        try:
            value = round(float(str(value).lower().replace("n/a", "").replace('"', "").replace("in", "").replace(",", "").replace("kg",
                          "").replace('$', "").replace("s/r", "").replace("bolt", "").replace("yd", "").replace("/", "").strip()), 2)
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


def markup(brand, product, format=True):
    def generatePrice(cost, multiplier, format):
        if format:
            price = math.ceil(cost * multiplier * 4) / 4
            if price == int(price):
                price -= 0.01
        else:
            price = round(cost * multiplier, 2)

        return float(price)

    try:
        useMAP = const.markup[brand]["useMAP"]

        consumerMarkup = const.markup[brand]["consumer"]
        tradeMarkup = const.markup[brand]["trade"]

        if product.type == "Pillow" and "consumer_pillow" in const.markup[brand]:
            consumerMarkup = const.markup[brand]["consumer_pillow"]
            tradeMarkup = const.markup[brand]["trade_pillow"]

        if product.european and "consumer_european" in const.markup[brand]:
            consumerMarkup = const.markup[brand]["consumer_european"]
            tradeMarkup = const.markup[brand]["trade_european"]

        if useMAP and product.map > 0:
            priceConsumer = generatePrice(product.map, 1, format)
        else:
            priceConsumer = generatePrice(product.cost, consumerMarkup, format)

        priceTrade = generatePrice(product.cost, tradeMarkup, format)

        if priceConsumer < 19.99:
            priceConsumer = 19.99
            priceTrade = 16.99

        priceSample = 5

        return (priceConsumer, priceTrade, priceSample)

    except Exception as e:
        debug.debug(brand, 1,
                    f"Price Error. Check if markups are defined properly. {str(e)}")
        return (0, 0, 0)


def getRelatedProducts(product):
    samePatterns = Product.objects.filter(
        manufacturer=product.manufacturer, type=product.type, pattern=product.pattern)

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
