from django.core.management.base import BaseCommand
from django.db.models import Max
from django.utils import formats

import json
import requests
import environ

from utils import debug, common
from vendor.models import Order

env = environ.Env()
SCALA_API_URL = env('SCALA_API_URL')
SCALA_API_URL = env('SCALA_API_URL')

BRAND = "Scalamandre"
PROCESS = "Scalamandre EDI"


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
        responseData = requests.post(
            f"{SCALA_API_URL}/Auth/authenticate",
            headers={'Content-Type': 'application/json'},
            data=json.dumps({
                "Username": env('SCALA_API_USERNAME'),
                "Password": "EuEc9MNAvDqvrwjgRaf55HCLr8c5B2^Ly%C578Mj*=CUBZ-Y4Q5&Sc_BZE?n+eR^gZzywWphXsU*LNn!",
            })
        )
        responseJSON = json.loads(responseData.text)
        self.token = responseJSON['Token']

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def requestAPI(self, url, payload):
        try:
            responseData = requests.post(
                f"{SCALA_API_URL}/{url}",
                headers={'Authorization': 'Bearer {}'.format(self.token)},
                json=payload
            )
            responseJSON = json.loads(responseData.text)
            return responseJSON
        except Exception as e:
            debug.warn(PROCESS, str(e))
            return None

    def submit(self):
        orders = Order.objects.filter(
            lineItems__product__manufacturer__brand=BRAND)

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
            if "2" in order.shippingMethod:
                shippingMethod = "UPS2"
            elif "over" in order.shippingMethod.lower():
                shippingMethod = "UPSN"
            else:
                shippingMethod = "UPSG"

            instructions = "\n".join(filter(None, [
                f"Ship Instruction: {order.customerNote}" if order.customerNote else None,
                f"Pack Instruction: DecoratorsBest/{order.shippingLastName}"
            ]))

            try:

                sampleArray = []
                orderArray = []

                for lineItem in order.lineItems.filter(product__manufacturer__brand=BRAND):
                    if lineItem.variant == "Sample" or lineItem.variant == "Free Sample":
                        sampleArray.append({
                            "ORDER_NO": int(order.po),
                            "ORDER_DATE": formats.date_format(order.orderDate, 'd-M-y'),
                            "SHIP_VIA_NO": shippingMethod,
                            "S_AND_H": 0,
                            "CUST_NO": "591267",
                            "SKU_REF1": lineItem.product.mpn,
                            "SALES_PRICE": 0,
                            "QTY": 1,
                            "SIZE_NAME": "STANDARD",
                            "USER_REF1": lineItem.product.mpn,
                            "STNAME": f"{order.shippingFirstName} {order.shippingLastName}",
                            "STADDR_1": order.shippingAddress1,
                            "STADDR_2": order.shippingAddress2,
                            "STCITY": order.shippingCity,
                            "STSTATE": common.provinceCode(order.shippingState),
                            "STCOUNTRY": "US",
                            "STPOSTAL": order.shippingZip,
                            "E_MAIL": "memos@decoratorsbest.com",
                            "ORDERNOTES": instructions,
                            "BRANCH": "NY",
                            "REQUIRESMGROK": False,
                            "COMPANY": 5,
                            "ORDERTYPE": "SCLL",
                            "SIDEMARK": "Decoratorsbest"
                        })

                    else:
                        orderArray.append({
                            "ITEMID": lineItem.product.mpn,
                            "LENGTHININCHES": lineItem.quantity,
                            "CARPETCOST": lineItem.product.cost,
                            "NOTES": [
                                {
                                    "MSGTYPE": "DELIVERY",
                                    "MESSAGESTR": instructions
                                }
                            ]
                        })

                if len(orderArray) > 0:
                    refData = self.requestAPI(
                        "/ScalaFeedAPI/SubmitOrder",
                        {
                            "MType": 1,
                            "MQuoteID": order.po,
                            "AccountID": "591267",
                            "QuoteJson": {
                                "ITEMDETAILS": orderArray,
                                "SHIPTO": [
                                    {
                                        "NAME": f"{order.shippingFirstName} {order.shippingLastName}",
                                        "ADDRESS1": order.shippingAddress1,
                                        "ADDRESS2": order.shippingAddress2,
                                        "CITY": order.shippingCity,
                                        "STATE": common.provinceCode(order.shippingState),
                                        "ZIP": order.shippingZip,
                                        "countrycode": "US",
                                        "phoneNumber1": None
                                    }
                                ],
                                "CO_ACCTNUM": "591267",
                                "COMPANY": "5",
                                "SUBMITTYPE": 1,
                                "UserEmail": "purchasing@decoratorsbest.com",
                                "FinalDest": {
                                    "Name": f"{order.shippingFirstName} {order.shippingLastName}",
                                    "Address1": order.shippingAddress1,
                                    "Address2": order.shippingAddress2,
                                    "City": order.shippingCity,
                                    "State": common.provinceCode(order.shippingState),
                                    "zipcode5": order.shippingZip,
                                    "ZipCode": order.shippingZip,
                                    "SideMark": "Decoratorsbest",
                                    "SideMark2": "Decoratorsbest",
                                    "Contact": "",
                                    "Notes": instructions,
                                    "countrycode": "US",
                                }
                            },
                            "UserName": "Decoratorsbest",
                            "UserEmail": "purchasing@decoratorsbest.com",
                        }
                    )

                    ref = refData[0]['WEBQUOTEID']
                    self.ref(order, ref)

                if len(sampleArray) > 0:
                    refData = self.requestAPI(
                        "/ScalaFeedAPI/SubmitSampleOrder",
                        {
                            "SampleOrderJson": {
                                "USERNAME": "Decoratorsbest",
                                "SAMPLEORDER": sampleArray
                            }
                        }
                    )

                    ref = refData[0]['SAMPLEORDERITEMS'][0]['ORDER_NO']
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
