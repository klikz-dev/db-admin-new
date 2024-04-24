from django.core.management.base import BaseCommand
from django.db.models import Max
from django.utils import formats

import os
import environ
import datetime
import pytz
import csv
import codecs
import pysftp
import paramiko

from utils import debug, common, const
from vendor.models import Order

env = environ.Env()

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Schumacher"
PROCESS = "Schumacher EDI"


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
            host=const.sftp[BRAND]["host"],
            port=const.sftp[BRAND]["port"],
            username=const.sftp[BRAND]["user"],
            password=const.sftp[BRAND]["pass"],
            cnopts=cnopts
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sftp.close()
        pass

    def submit(self):
        now = datetime.datetime.now(pytz.timezone("America/New_York"))
        fileName = f"PO_{now.strftime('%Y%m%d')}_{now.strftime('%H%M%S')}.csv"

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
        # manualPOs = [623685]
        # orders = Order.objects.filter(po__in=manualPOs)
        ### Manual Process for Missing Orders ###

        lines = []

        for order in orders:
            if "2" in order.shippingMethod:
                shippingMethod = "2nd Day"
            elif "over" in order.shippingMethod.lower():
                shippingMethod = "Overnight"
            else:
                shippingMethod = "Ground"

            try:
                lineItems = order.lineItems.filter(
                    product__manufacturer__brand=BRAND)
                for index, lineItem in enumerate(lineItems):

                    uom = lineItem.product.uom
                    email = "purchasing@decoratorsbest.com"
                    if lineItem.variant == "Sample" or lineItem.variant == "Free Sample":
                        uom = "MM (Sample)"
                        email = "memos@decoratorsbest.com"
                    elif uom == "Yard":
                        uom = "YD"
                    elif uom == "Roll":
                        uom = "RL"
                    elif uom == "Square Foot":
                        uom = "SQF"
                    else:
                        uom = "EA"

                    lines.append({
                        'PO_Number': order.po,
                        'PO_LINE_NUMBER': index + 1,
                        'ORDERED_ITEM': lineItem.product.mpn,
                        'ORDER_QUANTITY_UOM': uom,
                        'ORDERED_QUANTITY': lineItem.quantity,
                        'ORDER_DATE': formats.date_format(order.orderDate, 'd-M-y'),
                        'ACCOUNT_NUMBER': "106449",
                        'CUSTOMER_NAME': f"{order.shippingFirstName} {order.shippingLastName}",
                        'HDR_SHIP_ADDRESS1': order.shippingAddress1,
                        'HDR_SHIP_ADDRESS2': order.shippingAddress2,
                        'HDR_SHIP_SUITE': "",
                        'HDR_SHIP_CITY': order.shippingCity,
                        'HDR_SHIP_STATE': common.provinceCode(order.shippingState),
                        'HDR_SHIP_COUNTY': "",
                        'HDR_SHIP_ZIP': order.shippingZip,
                        'HDR_SHIP_COUNTRY': "US",
                        'HDR_SHIP_PHONE': order.shippingPhone,
                        'HDR_SHIP_METHOD': shippingMethod,
                        'HDR_SHIP_INSTRUCTIONS': order.customerNote,
                        'HDR_PACK_INSTRUCTIONS': f"DecoratorsBest/{order.shippingLastName}",
                        'ACK_EMAIL_ADDRESS': email,
                    })

                order.status = PROCESS if order.status == "New" else f"{order.status}, {PROCESS}"
                order.save()

            except Exception as e:
                debug.error(
                    PROCESS, f"Processing {order.po} failed. Terminiated {PROCESS}. {str(e)}")
                continue

        with open(f"{FILEDIR}/edi/schumacher/{fileName}", 'w', newline='') as file:
            headers = lines[0].keys()
            csvwriter = csv.DictWriter(file, fieldnames=headers)

            csvwriter.writeheader()

            for line in lines:
                csvwriter.writerow(line)

        self.upload(fileName)

    def upload(self, fileName):
        try:
            with self.sftp.cd('/schumacher/EDI/EDI_from_DB'):
                self.sftp.put(f"{FILEDIR}/edi/schumacher/{fileName}")

        except Exception as e:
            debug.error(
                PROCESS, f"Uploading {fileName} failed. Terminiated {PROCESS}. {str(e)}")

    def ref(self):
        files = self.sftp.listdir('/schumacher/EDI/EDI_to_DB')
        poAs = [file for file in files if 'POA' in file]

        for poA in poAs:
            try:
                self.sftp.get(f"/schumacher/EDI/EDI_to_DB/{poA}",
                              f"{FILEDIR}/edi/schumacher/{poA}")
                self.sftp.remove(f"/schumacher/EDI/EDI_to_DB/{poA}")
            except Exception as e:
                debug.error(
                    PROCESS, f"Downloading {poA} failed. Terminiated {PROCESS}. {str(e)}")
                continue

        for poA in poAs:
            f = open(f"{FILEDIR}/edi/schumacher/{poA}", "rb")
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
