from django.core.management.base import BaseCommand
from django.db.models import Max
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

from utils import debug, shopify, common

from vendor.models import Address, Customer, Order, LineItem, Product

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

        Address.objects.all().delete()
        Customer.objects.all().delete()
        LineItem.objects.all().delete()
        Order.objects.all().delete()

        shopifyManager = shopify.ShopifyManager()

        while True:

            lastOrderId = Order.objects.aggregate(
                Max('shopifyId'))['shopifyId__max']

            orders = shopifyManager.getOrders(lastOrderId=lastOrderId or 0)

            if len(orders) == 0:
                break

            # for order in tqdm(orders):
            def syncOrder(order):

                try:

                    # Addresses
                    def get_or_create_address(address_data):
                        unique_fields = {
                            'firstName': address_data['first_name'],
                            'lastName': address_data['last_name'],
                            'address1': address_data['address1'],
                            'city': address_data['city'],
                            'state': address_data['province'],
                            'zip': address_data['zip'],
                            'country': address_data['country'],
                        }

                        defaults = {
                            'company': address_data.get('company', ''),
                            'address2': address_data.get('address2', ''),
                            'phone': address_data.get('phone', ''),
                        }

                        return Address.objects.get_or_create(**unique_fields, defaults=defaults)

                    customerAddress, created = get_or_create_address(
                        order['customer']['default_address'])
                    shippingAddress, created = get_or_create_address(
                        order['shipping_address'])
                    billingAddress, created = get_or_create_address(
                        order['billing_address'])

                    # Customer
                    customer, created = Customer.objects.update_or_create(
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

                    # Order Type
                    hasOrder = any("Sample" not in item['variant_title']
                                   for item in order['line_items'])
                    hasSample = any("Sample" in item['variant_title']
                                    for item in order['line_items'])
                    orderType = "/".join(
                        filter(None, ["Order" if hasOrder else None, "Sample" if hasSample else None]))

                    shipping_lines = order.get('shipping_lines', [])
                    if shipping_lines:
                        shippingCost = shipping_lines[0]['price']
                        shippingMethod = shipping_lines[0]['title']
                    else:
                        shippingCost = 0
                        shippingMethod = "Free Shipping"

                    orderRef, created = Order.objects.update_or_create(
                        shopifyId=order['id'],
                        po=order['order_number'],

                        orderType=orderType,
                        email=order['email'],
                        phone=order['phone'],
                        customer=customer,

                        shippingAddress=shippingAddress,
                        billingAddress=billingAddress,

                        subTotal=order['total_line_items_price'],
                        discount=order['total_discounts'],
                        shippingCost=shippingCost,
                        tax=order['current_total_tax'],
                        total=order['total_price'],

                        shippingMethod=shippingMethod,
                        weight=round(order['total_weight'] / 453.592, 2),
                        orderDate=order['created_at'],

                        status=status,
                        reference=reference,
                        internalNote=internalNote,
                        customerNote=order['note'],
                    )

                    # Line Items
                    for lineItem in order['line_items']:
                        try:
                            product = Product.objects.get(
                                shopifyId=lineItem['product_id'])
                        except Product.DoesNotExist:
                            debug.warn(
                                PROCESS, f"Order #{order['order_number']} Product {lineItem['product_id']} not found.")
                            continue

                        if "Trade" in lineItem['variant_title']:
                            variant = "Trade"
                        elif "Free Sample" in lineItem['variant_title']:
                            variant = "Free Sample"
                        elif "Sample" in lineItem['variant_title']:
                            variant = "Sample"
                        else:
                            variant = "Consumer"

                        LineItem.objects.create(
                            order=orderRef,
                            product=product,

                            variant=variant,
                            quantity=lineItem['quantity'],

                            orderPrice=lineItem['price'],
                            orderDiscount=lineItem['total_discount'],
                            orderWeight=common.toFloat(
                                lineItem['grams'] / 453.592),
                        )

                    debug.log(
                        PROCESS, f"PO {order['order_number']} has been synced.")

                except Exception as e:
                    debug.warn(PROCESS, str(e))

            with ThreadPoolExecutor(max_workers=25) as executor:
                for order in orders:
                    executor.submit(syncOrder, order)
