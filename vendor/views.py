from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from datetime import datetime, timedelta

from .models import Inventory, Order, Product
from .serializers import InventorySerializer, OrderListSerializer, OrderDetailSerializer, OrderUpdateSerializer


class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer

    def list(self, request):
        inventories = Inventory.objects.all()

        sku = self.request.query_params.get('sku')
        if sku is not None:
            inventories = inventories.filter(sku=sku)

        page = self.paginate_queryset(inventories)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(inventories, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        inventories = Inventory.objects.all()

        inventory = get_object_or_404(inventories, pk=pk)
        serializer = InventorySerializer(
            instance=inventory, context={'request': request})

        return Response(serializer.data)


class OrderViewSet(viewsets.ModelViewSet):

    queryset = Order.objects.all()
    serializer_class = OrderListSerializer

    def list(self, request):
        orders = Order.objects.all().order_by('-orderDate')

        fr = self.request.query_params.get('from')
        to = self.request.query_params.get('to')
        if fr is not None and to is not None:
            orders = orders.filter(orderDate__range=(datetime.strptime(
                fr, '%y-%m-%d'), datetime.strptime(to, '%y-%m-%d') + timedelta(days=1)))

        po = self.request.query_params.get('po')
        if po is not None:
            orders = orders.filter(po=po)

        customer = self.request.query_params.get('customer')
        if customer is not None:
            orders = orders.filter(Q(shippingFirstName__icontains=customer) | Q(
                shippingLastName__icontains=customer) | Q(email__icontains=customer))

        manufacturer = self.request.query_params.get('manufacturer')
        if manufacturer is not None:
            orders = orders.filter(manufacturers__icontains=manufacturer)

        ref = self.request.query_params.get('ref')
        if ref is not None:
            orders = orders.filter(reference__icontains=ref)

        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        # orderRes = shopify.getOrderById(pk)

        # if orderRes.get('order'):
        #     try:
        #         common.importOrder(orderRes['order'])
        #     except Exception as e:
        #         debug.debug("Order", 1, str(e))

        orders = Order.objects.all()
        order = get_object_or_404(orders, pk=pk)
        serializer = OrderDetailSerializer(
            instance=order, context={'request': request})
        return Response(serializer.data)

    def update(self, request, pk=None):
        orders = Order.objects.all()
        order = get_object_or_404(orders, pk=pk)
        serializer = OrderUpdateSerializer(data=request.data, partial=True)

        if serializer.is_valid():
            serializer.update(
                instance=order, validated_data=serializer.validated_data)

            updatedOrder = get_object_or_404(orders, pk=pk)
            # shopify.updateOrderById(order.shopifyOrderId, updatedOrder)

            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
