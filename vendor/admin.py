from django.contrib import admin

from .models import Manufacturer, Type, Tag, Product, Image, Sync, Inventory


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
        'private'
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
        'parent'
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
        'type'
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
            'barcode',
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
        'manufacturer',
        'type',
        'published',
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
        'barcode',
    ]


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    fields = [
        'product',
        'url',
        'position'
    ]

    list_display = [
        'product',
        'url',
        'position'
    ]

    list_filter = [
        'position'
    ]

    search_fields = [
        'product',
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
