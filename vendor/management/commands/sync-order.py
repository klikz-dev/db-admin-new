from django.core.management.base import BaseCommand
from django.db.models import Max
from tqdm import tqdm

from utils import debug, shopify, common

from vendor.models import Customer, Order, LineItem, Product

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

    def address(self, address_data, prefix=''):
        def getKey(prefix, key):
            return key if not prefix else f'{prefix}{key[0].upper() + key[1:]}'

        return {
            getKey(prefix, 'address1'): address_data['address1'],
            getKey(prefix, 'city'): address_data['city'],
            getKey(prefix, 'state'): address_data['province'],
            getKey(prefix, 'zip'): address_data['zip'],
            getKey(prefix, 'country'): address_data['country'],
            getKey(prefix, 'firstName'): address_data['first_name'],
            getKey(prefix, 'lastName'): address_data['last_name'],
            getKey(prefix, 'company'): address_data.get('company', ''),
            getKey(prefix, 'address2'): address_data.get('address2', ''),
            getKey(prefix, 'phone'): address_data.get('phone', ''),
        }

    def order(self):

        shopifyManager = shopify.ShopifyManager()

        lastOrderId = Order.objects.aggregate(
            Max('shopifyId'))['shopifyId__max']

        orders = shopifyManager.getOrders(lastOrderId=lastOrderId or 0)

        if len(orders) == 0:
            return

        for index, order in enumerate(orders):

            # Addresses
            customerAddress = self.address(
                address_data=order['customer'].get('default_address', None) or order['shipping_address'])
            shippingAddress = self.address(
                address_data=order['shipping_address'], prefix='shipping')
            billingAddress = self.address(
                address_data=order['billing_address'] or order['shipping_address'], prefix='billing')

            # Customer
            customer, _ = Customer.objects.get_or_create(
                shopifyId=order['customer']['id'],
                defaults={
                    'email': order['customer']['email'],
                    **customerAddress,
                    'note': order['customer']['note'],
                    'tags': order['customer']['tags'],
                }
            )

            # Order Type
            hasOrder = any("Sample" not in str(item['variant_title'])
                           for item in order['line_items'])
            hasSample = any("Sample" in str(item['variant_title'])
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

            status = "Hold" if order['note'] else "New"

            orderRef, _ = Order.objects.update_or_create(
                shopifyId=order['id'],
                defaults={
                    "po": order['order_number'],

                    "orderType": orderType,
                    "email": order['email'],
                    "phone": order['phone'],

                    "customer": customer,

                    **shippingAddress,
                    **billingAddress,

                    "subTotal": order['total_line_items_price'],
                    "discount": order['total_discounts'],
                    "shippingCost": shippingCost,
                    "tax": order['current_total_tax'],
                    "total": order['total_price'],

                    "shippingMethod": shippingMethod,
                    "weight": round(order['total_weight'] / 453.592, 2),
                    "orderDate": order['created_at'],
                    "customerNote": order['note'],

                    "status": status,
                }
            )

            # Line Items
            manufacturers = []

            for lineItem in order['line_items']:
                try:
                    product = Product.objects.get(
                        shopifyId=lineItem['product_id'])
                except Product.DoesNotExist:
                    debug.warn(PROCESS,
                               f"Order #{order['order_number']} Product {lineItem['product_id']} not found.")
                    continue

                if product.manufacturer.name not in {m['name'] for m in manufacturers}:
                    manufacturers.append({
                        "brand": product.manufacturer.brand,
                        "name": product.manufacturer.name
                    })

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

            orderRef.manufacturers = manufacturers
            orderRef.save()

            debug.log(
                PROCESS, f"{index}/{len(orders)}: PO {order['order_number']} has been synced.")
