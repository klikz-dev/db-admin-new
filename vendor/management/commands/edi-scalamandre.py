from django.core.management.base import BaseCommand
from django.db.models import Max

from utils import debug, shopify

from vendor.models import Order

PROCESS = "EDI-Scalamandre"


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
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def submit(self):
        lastProcessed = Order.objects.filter(
            status__icontains="Scalamandre EDI").aggregate(Max('shopifyId'))['shopifyId__max']

        exceptions = [
            "Hold",
            "Back Order",
            "Cancel",
            "Processed",
            "CFA",
            "Call Manufacturer"
        ]

        orders = Order.objects.filter(shopifyId__gt=lastProcessed).filter(
            lineItems__product__manufacturer__brand="Scalamandre").exclude(status__in=exceptions)

        for order in orders:
            print(order.shopifyId)

            sampleArray = []
            orderArray = []

            instructions = "\n".join(filter(None, [
                f"Ship Instruction: {order.customerNote}" if order.customerNote else None,
                f"Pack Instruction: DecoratorsBest/{order.shippingLastName}"
            ]))

            for lineItem in order.lineItems.all():
                if lineItem.variant == "Sample" or lineItem.variant == "Free Sample":
                    sampleArray.append({
                        "ORDER_NO": order.po,
                        "ORDER_DATE": order.orderDate,
                        "SHIP_VIA_NO": order.shippingMethod,
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
                        "STSTATE": order.shippingState,
                        "STCOUNTRY": order.shippingCountry,
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

            print(orderArray)
            print(sampleArray)

            break
