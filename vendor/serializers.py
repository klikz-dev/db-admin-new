from rest_framework import serializers
from .models import Inventory, Order, LineItem, Product, Tracking, Image, Customer


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


# Tracking
class TrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tracking
        fields = '__all__'


# Line Items
class LineItemOrder(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['shopifyId', 'po', 'email', 'shippingFirstName', 'shippingLastName', 'shippingAddress1', 'shippingAddress2',
                  'shippingCity', 'shippingState', 'shippingZip', 'shippingCountry', 'shippingPhone', 'shippingMethod',
                  'status', 'orderType', 'total', 'manufacturers', 'reference', 'orderDate', 'internalNote', 'shippingMethod']


class LineItemListSerializer(serializers.ModelSerializer):
    order = LineItemOrder(many=False, read_only=True)
    product = ProductSerializer(many=False, read_only=True)

    class Meta:
        model = LineItem
        fields = '__all__'


class LineItemDetailSerializer(serializers.ModelSerializer):
    product = ProductSerializer(many=False, read_only=True)

    class Meta:
        model = LineItem
        fields = '__all__'


class LineItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineItem
        fields = ['backorder']


# Orders
class OrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['shopifyId', 'po', 'status', 'orderDate', 'orderType', 'email', 'shippingFirstName',
                  'shippingLastName', 'total', 'manufacturers', 'shippingMethod', 'reference', 'internalNote']


class OrderDetailSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(many=False, read_only=True)
    lineItems = LineItemDetailSerializer(many=True, read_only=True)
    trackings = TrackingSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = '__all__'


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['shippingFirstName', 'shippingLastName', 'shippingCompany', 'shippingAddress1', 'shippingAddress2',
                  'shippingCity', 'shippingState', 'shippingZip', 'shippingCountry', 'shippingPhone', 'shippingMethod',
                  'total', 'internalNote', 'status', 'reference']
