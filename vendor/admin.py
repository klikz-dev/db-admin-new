from django.contrib import admin

from .models import Manufacturer, Type, Tag, Product, Image, Sync, Inventory, Customer, Order, LineItem, Tracking, Roomvo


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    fields = [
        'name',
        'brand',
        'private'
    ]

    list_display = [
        'name',
        'brand',
        'private',
        'productsCount'
    ]

    list_filter = [
        'brand',
        'private'
    ]

    search_fields = [
        'name',
        'brand'
    ]


@admin.register(Type)
class TypeAdmin(admin.ModelAdmin):
    fields = [
        'name',
        'parent'
    ]

    list_display = [
        'name',
        'parent',
        'productsCount'
    ]

    list_filter = [
        'parent'
    ]

    search_fields = [
        'name',
        'parent'
    ]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    fields = [
        'name',
        'type'
    ]

    list_display = [
        'name',
        'type',
        'productsCount'
    ]

    list_filter = [
        'type'
    ]

    search_fields = [
        'name',
        'type'
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Primary Keys', {'fields': [
            'mpn',
            'sku',
            'shopifyId',
            'shopifyHandle',
        ]}),
        ('Content', {'fields': [
            'title',
            'description',
        ]}),
        ('Data', {'fields': [
            'pattern',
            'color',
            'collection',
            'usage',
            'disclaimer',
            'width',
            'length',
            'height',
            'size',
            'repeatH',
            'repeatV',
            'yardsPR',
            'content',
            'match',
            'material',
            'finish',
            'care',
            'country',
            'specs',
            'features',
        ]}),
        ('Pricing', {'fields': [
            'uom',
            'minimum',
            'increment',
        ]}),
        ('Category', {'fields': [
            'manufacturer',
            'type',
            'tags',
        ]}),
        ('Variant', {'fields': [
            'consumerId',
            'tradeId',
            'sampleId',
            'freeSampleId',
            'cost',
            'consumer',
            'trade',
            'sample',
            'compare',
            'weight',
            'upc',
        ]}),
        ("Status", {'fields': [
            'published',
        ]}),
    ]

    list_display = [
        'sku',
        'shopifyId',
        'title',
        'manufacturer',
        'type',
        'published'
    ]

    list_filter = [
        'manufacturer__brand',
        'published',
        'type',
        'manufacturer',
        'uom'
    ]

    search_fields = [
        'mpn',
        'sku',
        'title',
        'description',
        'shopifyId',
        'consumerId',
        'tradeId',
        'sampleId',
        'freeSampleId',
        'upc',
    ]


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    autocomplete_fields = [
        'product',
    ]

    fields = [
        'shopifyId',
        'url',
        'position',
        'product',
        'hires',
    ]

    list_display = [
        'shopifyId',
        'url',
        'position',
        'product',
        'hires',
    ]

    list_filter = [
        'product__manufacturer__brand',
        'position',
        'hires',
    ]

    search_fields = [
        'shopifyId',
        'product__shopifyId',
        'product__shopifyHandle',
        'product__sku',
        'product__mpn',
        'product__title',
        'url'
    ]


@admin.register(Sync)
class SyncAdmin(admin.ModelAdmin):
    fields = [
        'productId',
        'type',
    ]

    list_display = [
        'productId',
        'type',
    ]

    list_filter = [
        'type'
    ]

    search_fields = [
        'productId',
    ]


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    fields = [
        'sku',
        'quantity',
        'type',
        'note',
        'brand'
    ]

    list_display = [
        'sku',
        'quantity',
        'type',
        'note',
        'brand'
    ]

    list_filter = [
        'type',
        'brand'
    ]

    search_fields = [
        'sku',
        'note',
        'brand'
    ]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    fields = [
        'shopifyId',
        'email',
        'firstName',
        'lastName',
        'company',
        'address1',
        'address2',
        'city',
        'state',
        'zip',
        'country',
        'phone',
        'note',
        'tags',
    ]

    list_display = [
        'email',
        'firstName',
        'lastName',
        'phone',
        'tags',
    ]

    list_filter = [
        'tags',
    ]

    search_fields = [
        'shopifyId',
        'email',
        'firstName',
        'lastName',
        'phone',
        'note',
        'tags',
    ]


class LineItemInline(admin.TabularInline):
    model = LineItem
    extra = 0

    autocomplete_fields = [
        'product',
    ]

    fields = [
        'product',
        'variant',
        'quantity',
        'orderPrice',
    ]


class TrackingInline(admin.TabularInline):
    model = Tracking
    extra = 0

    fields = [
        'brand',
        'company',
        'number',
    ]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    autocomplete_fields = [
        'customer',
    ]

    inlines = [LineItemInline, TrackingInline]

    fieldsets = [
        ('Primary Keys', {'fields': [
            'shopifyId',
            'po',
            'orderType',
            'email',
            'phone',
            'customer',
        ]}),
        ('Shipping Address', {'fields': [
            'shippingFirstName',
            'shippingLastName',
            'shippingCompany',
            'shippingAddress1',
            'shippingAddress2',
            'shippingCity',
            'shippingState',
            'shippingZip',
            'shippingCountry',
            'shippingPhone',
        ]}),
        ('Billing Address', {'fields': [
            'billingFirstName',
            'billingLastName',
            'billingCompany',
            'billingAddress1',
            'billingAddress2',
            'billingCity',
            'billingState',
            'billingZip',
            'billingCountry',
            'billingPhone',
        ]}),
        ('Details', {'fields': [
            'subTotal',
            'discount',
            'shippingCost',
            'tax',
            'total',
            'shippingMethod',
            'weight',
            'orderDate',
        ]}),
        ('Status', {'fields': [
            'status',
            'reference',
            'internalNote',
            'customerNote',
            'manufacturers',
        ]}),
    ]

    list_display = [
        'po',
        'orderType',
        'customer',
        'total',
        'status',
    ]

    list_filter = [
        'orderType',
        'lineItems__product__manufacturer__brand',
        'shippingMethod',
        'status',
    ]

    search_fields = [
        'shopifyId',
        'po',
        'orderType',
        'email',
        'phone',
    ]


@admin.register(LineItem)
class LineItemAdmin(admin.ModelAdmin):
    autocomplete_fields = [
        'order',
        'product',
    ]

    fields = [
        'order',
        'product',
        'variant',
        'quantity',
        'orderPrice',
        'orderDiscount',
        'orderWeight',
        'tracking',
    ]

    list_display = [
        'order',
        'product',
        'variant',
        'quantity',
    ]

    list_filter = [
        'variant',
    ]

    search_fields = [
        'variant',
    ]


@admin.register(Tracking)
class TrackingAdmin(admin.ModelAdmin):
    autocomplete_fields = [
        'order',
    ]

    fields = [
        'order',
        'brand',
        'company',
        'number',
    ]

    list_display = [
        'order',
        'brand',
        'company',
        'number',
    ]

    list_filter = [
        'company',
        'brand',
    ]

    search_fields = [
        'order__shopifyId',
        'number',
    ]


@admin.register(Roomvo)
class RoomvoAdmin(admin.ModelAdmin):
    fields = [
        'sku',
        'name',
        'availability',

        'width',
        'length',
        'thickness',

        'dimension_display',
        'horizontal_repeat',
        'vertical_repeat',
        'layout',

        'brand',
        'product_type',

        'filter_category',
        'filter_style',
        'filter_color',
        'filter_subtype',

        'link',
        'image',

        'cart_id',
        'cart_id_trade',
        'cart_id_sample',
        'cart_id_free_sample'
    ]

    list_display = (
        'sku',
        'name',
        'width',
        'length',
        'thickness',
        'dimension_display',
        'brand',
        'product_type',
        'link'
    )

    list_filter = [
        'brand',
        'product_type',
        'filter_category',
        'filter_style',
        'filter_color',
        'filter_subtype',
    ]

    search_fields = [
        'sku',
        'name',
        'dimension_display',
        'layout',
        'brand',
        'product_type',
        'link',
        'filter_category',
        'filter_style',
        'filter_color',
        'filter_subtype',
        'cart_id',
        'cart_id_trade',
        'cart_id_sample',
        'cart_id_free_sample'
    ]
