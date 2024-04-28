import json
from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
from django.utils.timezone import make_aware

import os
import requests
import environ

from utils import debug

from vendor.models import Order

env = environ.Env()
KLAVIYO_KEY = env('KLAVIYO_KEY')

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"
PROCESS = "Klaviyo"


class Command(BaseCommand):
    help = f"Run {PROCESS}"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "sample-reminder" in options['functions']:
            with Processor() as processor:
                processor.sampleReminder()


class Processor:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def sampleReminder(self):

        date_fourteen_days_ago = (datetime.now() - timedelta(days=14)).date()

        start_of_day = make_aware(datetime.combine(
            date_fourteen_days_ago, datetime.min.time()))
        end_of_day = make_aware(datetime.combine(
            date_fourteen_days_ago, datetime.max.time()))

        orders = Order.objects.exclude(orderType="Order").filter(
            status="Processed", orderDate__range=(start_of_day, end_of_day))

        for order in orders:
            email = order.email
            firstName = order.shippingFirstName
            lastName = order.shippingLastName

            lineItems = order.lineItems.all()
            sampleItems = lineItems.filter(variant="Sample")
            if len(sampleItems) == 0:
                continue

            product = sampleItems[0].product

            sku = product.sku
            title = product.title
            image = product.images.get(position=1)

            data = {
                "dp": {
                    "actual_oid": order.po,
                    "t": title,
                    "img": image.url,
                    "sku": sku,
                    "u": f"https://www.decoratorsbest.com/products/{product.shopifyHandle}",
                    "unitprice": f"{product.consumer}",
                    "pricetype": f"Per {product.uom}"
                }
            }

            self.klaviyo(
                templateId="UKA5M2",
                subject="Have You Received Your Samples?",
                data=data,
                customer=f"{firstName} {lastName}",
                email=email
            )

    def klaviyo(self, templateId, subject, data, customer, email):
        payload = {
            'api_key': KLAVIYO_KEY,
            'from_email': 'orders@decoratorsbest.com',
            'from_name': 'DecoratorsBest',
            'subject': subject,
            'to': json.dumps([
                {'email': email, "name": customer}
            ]),
            'context': json.dumps(data)
        }

        response = requests.post(
            f'https://a.klaviyo.com/api/v1/email-template/{templateId}/send',
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data=payload)

        debug.log(PROCESS, str(response.text))
