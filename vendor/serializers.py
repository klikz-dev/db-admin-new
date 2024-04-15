from rest_framework import serializers
from .models import Inventory, Order, LineItem, Product, Image, Customer


class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = '__all__'


# Customer
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'


# Image
class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = '__all__'


# Product
class ProductSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = '__all__'


# Line Items
class LineItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(many=False, read_only=True)

    class Meta:
        model = LineItem
        fields = '__all__'


# Orders
class OrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['shopifyId', 'po', 'orderType', 'email', 'shippingFirstName', 'shippingLastName', 'total',
                  'shippingMethod', 'status', 'reference', 'orderDate', 'internalNote', 'manufacturers', 'lineItems']


class OrderDetailSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(many=False, read_only=True)
    lineItems = LineItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = '__all__'


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['shippingFirstName', 'shippingLastName', 'shippingCompany', 'shippingAddress1', 'shippingAddress2',
                  'shippingCity', 'shippingState', 'shippingZip', 'shippingCountry', 'shippingPhone', 'shippingMethod',
                  'total', 'internalNote', 'customerNote', 'status', 'manufacturers', 'reference']
