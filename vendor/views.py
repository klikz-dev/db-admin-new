from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Max

from datetime import datetime, timedelta

from .models import Inventory, Order, LineItem
from .serializers import InventorySerializer
from .serializers import OrderListSerializer
from .serializers import OrderDetailSerializer
from .serializers import OrderUpdateSerializer
from .serializers import LineItemListSerializer
from .serializers import LineItemDetailSerializer
from .serializers import LineItemUpdateSerializer


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

        type = self.request.query_params.get('type')
        if type is not None:
            if type == "s":
                orders = orders.filter(lineItems__variant__icontains="Sample")
            else:
                orders = orders.exclude(lineItems__variant__icontains="Sample")

        brand = self.request.query_params.get('brand')
        if brand is not None:
            lastProcessed = orders.filter(
                status__icontains=f"{brand} OM").aggregate(Max('shopifyId'))['shopifyId__max'] or 0
            orders = orders.filter(shopifyId__gt=lastProcessed).exclude(
                Q(status__icontains='Processed') |
                Q(status__icontains='Cancel') |
                Q(status__icontains='Hold') |
                Q(status__icontains='Call') |
                Q(status__icontains='Return') |
                Q(status__icontains='Discontinued') |
                Q(status__icontains='Back') |
                Q(status__icontains='B/O') |
                Q(status__icontains='Manually') |
                Q(status__icontains='CFA')
            ).filter(manufacturers__icontains=brand)

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

            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class LineItemViewSet(viewsets.ModelViewSet):

    queryset = LineItem.objects.all()
    serializer_class = LineItemListSerializer

    def list(self, request):
        lineItems = LineItem.objects.all()

        # Filter by Brand Name
        brand = self.request.query_params.get('brand')
        if brand is not None:
            lastProcessed = Order.objects.filter(
                status__icontains=f"{brand} Reference# Needed").aggregate(Max('shopifyId'))['shopifyId__max'] or 0

            lineItems = lineItems.filter(order__shopifyId__gt=lastProcessed).filter(
                product__manufacturer__brand=brand)
        ######################

        # Filter by Processor Type
        type = self.request.query_params.get('type')
        if type == 's':
            lineItems = lineItems.filter(variant__icontains='Sample')
        if type == 'o':
            lineItems = lineItems.exclude(variant__icontains='Sample')
        ###########################

        # Filter by Status
        lineItems = lineItems.exclude(
            Q(order__status__icontains='Processed') |
            Q(order__status__icontains='Cancel') |
            Q(order__status__icontains='Hold') |
            Q(order__status__icontains='Call') |
            Q(order__status__icontains='Return') |
            Q(order__status__icontains='Discontinued') |
            Q(order__status__icontains='Back') |
            Q(order__status__icontains='B/O') |
            Q(order__status__icontains='Manually') |
            Q(order__status__icontains='CFA')
        )
        ###########################

        page = self.paginate_queryset(lineItems)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(lineItems, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        lineItems = LineItem.objects.all()
        lineItem = get_object_or_404(lineItems, pk=pk)
        serializer = LineItemDetailSerializer(
            instance=lineItem, context={'request': request})
        return Response(serializer.data)

    def update(self, request, pk=None):
        lineItems = LineItem.objects.all()
        lineItem = get_object_or_404(lineItems, pk=pk)
        serializer = LineItemUpdateSerializer(data=request.data, partial=True)

        if serializer.is_valid():
            serializer.update(
                instance=lineItem, validated_data=serializer.validated_data)

            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
