from django.core.management.base import BaseCommand
from django.db.models import Max
from tqdm import tqdm

from utils import debug, shopify

from vendor.models import Address, Customer, Order

PROCESS = "Sync-Order"


class Command(BaseCommand):
    help = f"Run {PROCESS}"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        with Processor() as processor:
            processor.order()


class Processor:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def order(self):
        shopifyManager = shopify.ShopifyManager()

        while True:

            lastOrderId = Order.objects.aggregate(
                Max('shopifyId'))['shopifyId__max']

            orders = shopifyManager.getOrders(lastOrderId=lastOrderId or '')

            if len(orders) == 0:
                break

            for order in orders:
                print(order)

                customerAddress = Address.objects.get_or_create(
                    firstName=order['customer']['default_address']['first_name'],
                    lastName=order['customer']['default_address']['last_name'],
                    company=order['customer']['default_address']['company'],
                    address1=order['customer']['default_address']['address1'],
                    address2=order['customer']['default_address']['address2'],
                    city=order['customer']['default_address']['city'],
                    state=order['customer']['default_address']['province'],
                    zip=order['customer']['default_address']['zip'],
                    country=order['customer']['default_address']['country'],
                    phone=order['customer']['default_address']['phone'],
                )

                shippingAddress = Address.objects.get_or_create(
                    firstName=order['shipping_address']['first_name'],
                    lastName=order['shipping_address']['last_name'],
                    company=order['shipping_address']['company'],
                    address1=order['shipping_address']['address1'],
                    address2=order['shipping_address']['address2'],
                    city=order['shipping_address']['city'],
                    state=order['shipping_address']['province'],
                    zip=order['shipping_address']['zip'],
                    country=order['shipping_address']['country'],
                    phone=order['shipping_address']['phone'],
                )

                billingAddress = Address.objects.get_or_create(
                    firstName=order['billing_address']['first_name'],
                    lastName=order['billing_address']['last_name'],
                    company=order['billing_address']['company'],
                    address1=order['billing_address']['address1'],
                    address2=order['billing_address']['address2'],
                    city=order['billing_address']['city'],
                    state=order['billing_address']['province'],
                    zip=order['billing_address']['zip'],
                    country=order['billing_address']['country'],
                    phone=order['billing_address']['phone'],
                )

                customer = Customer.objects.get_or_create(
                    shopifyId=order['customer']['id'],
                    email=order['customer']['email'],
                    firstName=order['customer']['first_name'],
                    lastName=order['customer']['last_name'],
                    phone=order['customer']['phone'],
                    address=customerAddress,
                    note=order['customer']['note'],
                    tags=order['customer']['tags'],
                )

                status = ''
                reference = ''
                internalNote = ''
                for attr in order['note_attributes']:
                    if attr['name'] == 'Status':
                        status = attr['value']
                    if attr['name'] == 'ReferenceNumber':
                        reference = attr['value']
                    if attr['name'] == 'CSNote':
                        internalNote = attr['value']

                Order.objects.create(
                    shopifyId=order['id'],
                    po=order['order_number'],

                    orderType=order['orderType'],  # To do
                    email=order['email'],
                    phone=order['phone'],
                    customer=customer,

                    shippingAddress=shippingAddress,
                    billingAddress=billingAddress,

                    subTotal=order['total_line_items_price'],
                    discount=order['total_discount'],
                    shippingCost=order['shipping_lines'][0]['price'],
                    tax=order['current_total_tax'],
                    total=order['total_price'],

                    shippingMethod=order['shipping_lines'][0]['title'],
                    weight=round(order['total_weight'] / 453.592, 2),
                    orderDate=order['created_at'],

                    status=status,
                    reference=reference,
                    internalNote=internalNote,
                    customerNote=order['note'],
                )

                break

            break
