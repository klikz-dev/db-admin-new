from django.core.management.base import BaseCommand
from django.db.models import Max
from django.utils import formats

import json
import requests
import environ

from utils import debug, common
from vendor.models import Order

env = environ.Env()
PHILLIPS_API_URL = env('PHILLIPS_API_URL')
PHILLIPS_API_KEY = env('PHILLIPS_API_KEY')
PHILLIPS_API_USERNAME = env('PHILLIPS_API_USERNAME')
PHILLIPS_API_PASSWORD = env('PHILLIPS_API_PASSWORD')

BRAND = "Phillips Collection"
PROCESS = "Phillips Collection EDI"


class Command(BaseCommand):
    help = f"Run {PROCESS}"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "submit" in options['functions']:
            with Processor() as processor:
                processor.submit()


class Processor:
    def __init__(self):
        responseData = requests.request(
            "POST",
            f"{PHILLIPS_API_URL}/auth",
            headers={
                'Content-type': 'application/json',
                'x-api-key': PHILLIPS_API_KEY
            },
            data=json.dumps({
                "email": PHILLIPS_API_USERNAME,
                "password": PHILLIPS_API_PASSWORD
            })
        )
        responseJSON = json.loads(responseData.text)
        self.token = responseJSON['data']['token']

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def requestAPI(self, url, payload):
        try:
            responseData = requests.post(
                f"{PHILLIPS_API_URL}/{url}",
                headers={
                    'x-api-key': PHILLIPS_API_KEY,
                    'Authorization': "Bearer {}".format(self.token)
                },
                json=payload
            )
            responseJSON = json.loads(responseData.text)
            return responseJSON
        except Exception as e:
            debug.warn(PROCESS, str(e))
            return None

    def submit(self):
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
        # manualPOs = [616198, 616802, 621039, 623489]
        # orders = Order.objects.filter(po__in=manualPOs)
        ### Manual Process for Missing Orders ###

        for order in orders:

            address = ", ".join(filter(
                None, [order.shippingAddress1, order.shippingAddress2, order.shippingCompany]))

            try:
                lineItems = []
                for lineItem in order.lineItems.filter(product__manufacturer__brand=BRAND):
                    lineItems.append({
                        'itemno': lineItem.product.mpn,
                        'qtyorder': lineItem.quantity
                    })

                refData = self.requestAPI(url="/ecomm/orders", payload={
                    'reference': f"PO #{order.po}",
                    'shipto': {
                        'shipname': f"{order.shippingFirstName} {order.shippingLastName}",
                        'address': address,
                        'city': order.shippingCity,
                        'state': order.shippingState,
                        'zip': order.shippingZip,
                        'country': "USA",
                        'phone': order.shippingPhone,
                        'fax': '',
                        'email': '',
                    },
                    'shipcontact': {
                        'name': "DecoratorsBest Orders Department",
                        'email': 'purchasing@decoratorsbest.com',
                        'phone': ''
                    },
                    'items': lineItems
                })

                ref = refData['data']['_id']
                self.ref(order, ref)

                order.status = PROCESS if order.status == "New" else f"{order.status}, {PROCESS}"
                order.save()

            except Exception as e:
                debug.error(
                    PROCESS, f"Processing {order.po} failed. Terminiated {PROCESS}. {str(e)}")
                break

    def ref(self, order, ref):
        order.reference = "\n".join(filter(None, [
            order.reference,
            f"{PROCESS}: {ref}"
        ]))
        order.save()

        debug.log(
            PROCESS, f"PO #{order.po} reference number: {order.reference}")
