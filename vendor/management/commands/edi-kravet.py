from django.core.management.base import BaseCommand
from django.db.models import Max
from django.utils import formats

import os
import environ
import datetime
import pytz
import csv
import codecs
import xml.dom.minidom as MD
import xml.etree.ElementTree as ET
from ftplib import FTP

from utils import debug, common, const, shopify
from vendor.models import Order, Tracking

env = environ.Env()

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Kravet"
PROCESS = "Kravet EDI"


class Command(BaseCommand):
    help = f"Run {PROCESS}"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "submit" in options['functions']:
            with Processor() as processor:
                processor.submit()

        if "ref" in options['functions']:
            with Processor() as processor:
                processor.ref()

        if "tracking" in options['functions']:
            with Processor() as processor:
                processor.tracking()


class Processor:
    def __init__(self):
        self.ftp = FTP(const.ftp[BRAND]["host"])
        self.ftp.login(const.ftp[BRAND]["user"], const.ftp[BRAND]["pass"])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ftp.close()
        pass

    def submit(self):
        now = datetime.datetime.now(pytz.timezone("America/New_York"))
        fileName = f"KravetEDI_{now.strftime('%Y%m%d')}_{now.strftime('%H%M%S')}.xml"

        orders = Order.objects.filter(
            lineItems__product__manufacturer__brand=BRAND).distinct()

        lastProcessed = orders.filter(status__icontains=PROCESS).aggregate(
            Max('shopifyId'))['shopifyId__max'] or 1

        exceptions = [
            "Processed",
            "Processed Refund",
            "Processed Cancel",
            "Processed Return",
            "Cancel",
            "Hold",
            "Call",
            "Return",
            "Discontinued",
            "BackOrder",
            "Manually",
            "CFA",
        ]

        orders = orders.filter(shopifyId__gt=lastProcessed).exclude(
            status__in=exceptions)

        ### Manual Process for Missing Orders ###
        # manualPOs = [623815, 623740, 623462, 623454]
        # orders = Order.objects.filter(po__in=manualPOs)
        ### Manual Process for Missing Orders ###

        root = ET.Element("KFI_ORDER_LINE_XML")
        channel = ET.SubElement(root, "LIST_G_HDR")

        for order in orders:
            if "2" in order.shippingMethod:
                shippingMethod = "2nd Day"
            elif "over" in order.shippingMethod.lower():
                shippingMethod = "Overnight"
            else:
                shippingMethod = "Ground"

            address = ", ".join(filter(
                None, [order.shippingAddress1, order.shippingAddress2, order.shippingCompany]))

            email = "PURCHASING@DECORATORSBEST.COM" if "Order" in order.orderType else "MEMOS@DECORATORSBEST.COM"

            try:

                item = ET.SubElement(channel, "G_HDR")

                ET.SubElement(
                    item, "HDR_CUSTOMER_PO").text = f"{order.po}"
                ET.SubElement(
                    item, "CREATION_DATE").text = formats.date_format(order.orderDate, 'd-M-y').upper()
                ET.SubElement(
                    item, "ACCOUNT_NUMBER").text = "10180317"
                ET.SubElement(
                    item, "CONTACT_NAME").text = f"{order.shippingFirstName} {order.shippingLastName}".upper()
                ET.SubElement(
                    item, "CONT_PHONE_NUMBER").text = f'{order.shippingPhone.replace("+1", "").replace("-", "").replace(" ", "")}'
                ET.SubElement(
                    item, "HDR_SHIP_ADDRESS1").text = f"{order.shippingFirstName} {order.shippingLastName}".upper()
                ET.SubElement(
                    item, "HDR_SHIP_ADDRESS2").text = f"{address}".upper()
                ET.SubElement(
                    item, "HDR_SHIP_CITY").text = f"{order.shippingCity}".upper()
                ET.SubElement(
                    item, "HDR_SHIP_STATE").text = f"{common.provinceCode(order.shippingState)}"
                ET.SubElement(
                    item, "HDR_SHIP_COUNTY").text = ""
                ET.SubElement(
                    item, "HDR_SHIP_ZIP").text = f"{order.shippingZip}".upper()
                ET.SubElement(
                    item, "HDR_SHIP_COUNTRY").text = "US"
                ET.SubElement(
                    item, "HDR_SHIP_METHOD").text = f"{shippingMethod}".upper()
                ET.SubElement(
                    item, "HDR_SHIP_INSTRUCTIONS").text = f"{order.customerNote}".upper()
                ET.SubElement(
                    item, "HDR_PACK_INSTRUCTIONS").text = f"DecoratorsBest/{order.shippingLastName}".upper()
                ET.SubElement(
                    item, "ACK_EMAIL_ADDRESS").text = email

                lines = ET.SubElement(item, "LIST_G_LINES")

                lineItems = order.lineItems.filter(
                    product__manufacturer__brand=BRAND)
                for index, lineItem in enumerate(lineItems):

                    mpn = lineItem.product.mpn
                    uom = lineItem.product.uom
                    if lineItem.variant == "Sample" or lineItem.variant == "Free Sample":
                        mpn = mpn[0: -2] + ".M"
                        uom = "EA"
                    elif uom == "Yard":
                        uom = "YD"
                    elif uom == "Roll":
                        uom = "RL"
                    elif uom == "Square Foot":
                        uom = "SQF"
                    else:
                        uom = "EA"

                    line = ET.SubElement(lines, "G_LINES")
                    ET.SubElement(
                        line, "LINE_CUSTOMER_PO").text = f"{order.po}"
                    ET.SubElement(
                        line, "PO_LINE_NUMBER").text = f"{index + 1}"
                    ET.SubElement(
                        line, "ORDERED_ITEM").text = f"{mpn}".upper()
                    ET.SubElement(
                        line, "ORDER_QUANTITY_UOM").text = f"{uom}"
                    ET.SubElement(
                        line, "ORDERED_QUANTITY").text = f"{lineItem.quantity}"
                    ET.SubElement(
                        line, "LINE_SHIP_ADDRESS1").text = ""
                    ET.SubElement(
                        line, "LINE_SHIP_ADDRESS2").text = ""
                    ET.SubElement(
                        line, "LINE_SHIP_CITY").text = ""
                    ET.SubElement(
                        line, "LINE_SHIP_STATE").text = ""
                    ET.SubElement(
                        line, "LINE_SHIP_COUNTY").text = ""
                    ET.SubElement(
                        line, "LINE_SHIP_ZIP").text = ""
                    ET.SubElement(
                        line, "LINE_SHIP_COUNTRY").text = ""
                    ET.SubElement(
                        line, "LINE_SHIP_METHOD").text = ""
                    ET.SubElement(
                        line, "LINE_SHIP_INSTRUCTIONS").text = ""
                    ET.SubElement(
                        line, "LINE_PACK_INSTRUCTIONS").text = ""

                order.status = PROCESS if order.status == "New" else f"{order.status}, {PROCESS}"
                order.save()

            except Exception as e:
                debug.error(
                    PROCESS, f"Processing {order.po} failed. Terminiated {PROCESS}. {str(e)}")
                continue

        tree_str = ET.tostring(root, encoding='utf-8')

        tree_dom = MD.parseString(tree_str)
        pretty_tree = tree_dom.toprettyxml(indent="\t")

        with open(f"{FILEDIR}/edi/kravet/{fileName}", 'w', encoding="UTF-8") as file:
            file.write(pretty_tree)

        self.upload(fileName)

    def upload(self, fileName):
        self.ftp.cwd("/EDI FROM ALL DECOR/Live")

        with open(f"{FILEDIR}/edi/kravet/{fileName}", 'rb') as file:
            try:
                self.ftp.storbinary(f"STOR {fileName}", file)
            except Exception as e:
                debug.error(
                    PROCESS, f"Uploading {fileName} failed. Terminiated {PROCESS}. {str(e)}")

    def ref(self):
        self.ftp.cwd("/EDI TO ALL DECOR/ACK")

        files = self.ftp.nlst()
        ackExts = [file for file in files if 'AckExt' in file]

        for ackExt in ackExts:
            with open(f"{FILEDIR}/edi/kravet/{ackExt}", 'wb') as file:
                try:
                    def write_to_file(data):
                        file.write(data)

                    self.ftp.retrbinary(f"RETR {ackExt}", write_to_file)
                    self.ftp.delete(ackExt)
                except Exception as e:
                    debug.error(
                        PROCESS, f"Downloading {ackExt} failed. Terminiated {PROCESS}. {str(e)}")
                    continue

        for ackExt in ackExts:
            f = open(f"{FILEDIR}/edi/kravet/{ackExt}", "rb")
            cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
            for row in cr:
                if row[0] == "Customer PO Number":
                    continue

                try:
                    order = Order.objects.get(po=row[0])
                except Order.DoesNotExist:
                    continue

                if PROCESS not in str(order.reference):
                    order.reference = "\n".join(filter(None, [
                        order.reference,
                        f"{PROCESS}: {row[2]}"
                    ]))
                    order.save()

                    debug.log(
                        PROCESS, f"PO #{order.po} reference number: {order.reference}")

    def tracking(self):
        self.ftp.cwd("/EDI TO ALL DECOR")

        files = self.ftp.nlst()
        shipExts = [file for file in files if 'ShipExt' in file]

        for shipExt in shipExts:
            with open(f"{FILEDIR}/edi/kravet/{shipExt}", 'wb') as file:
                try:
                    def write_to_file(data):
                        file.write(data)

                    self.ftp.retrbinary(f"RETR {shipExt}", write_to_file)
                    self.ftp.delete(shipExt)
                except Exception as e:
                    debug.error(
                        PROCESS, f"Downloading {shipExt} failed. Terminiated {PROCESS}. {str(e)}")
                    continue

        for shipExt in shipExts:
            f = open(f"{FILEDIR}/edi/kravet/{shipExt}", "rb")
            cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
            for row in cr:
                if row[0] == "Customer PO #":
                    continue

                try:
                    order = Order.objects.get(po=row[0])
                except Order.DoesNotExist:
                    continue

                number = row[7]
                company = "FedEx" if "FedEx" in row[8] else "USPS" if "USPS" in row[8] else "UPS"

                Tracking.objects.update_or_create(
                    order=order,
                    brand=BRAND,
                    company=company,
                    number=number
                )

                # Upload Tracking to Shopify
                common.addTracking(order=order, brand=BRAND,
                                   number=number, company=company)
