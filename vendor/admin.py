from django.contrib import admin

from .models import Manufacturer, Type, Tag, Product, Variant, Image, Sync


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
            'shopifyId',
            'shopifyHandle',
        ]}),
        ('Content', {'fields': [
            'title',
            'description',
        ]}),
        ('Data', {'fields': [
            'pattern',
            'collection',
            'usage',
            'disclaimer',
            'width',
            'length',
            'height',
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
        ('Category', {'fields': [
            'manufacturer',
            'type',
            'tags',
        ]}),
        ("Status", {'fields': [
            'published',
        ]}),
    ]

    list_display = [
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
        'published'
    ]

    search_fields = [
        'title',
        'description',
        'shopifyId',
        'consumerId',
        'tradeId',
        'sampleId',
        'freeSampleId',
        'barcode',
    ]


@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Primary Keys', {'fields': [
            'shopifyId',
            'product',
        ]}),
        ('Option', {'fields': [
            'color',
            'size',
            'type',
        ]}),
        ('Data', {'fields': [
            'mpn',
            'sku',
            'cost',
            'price',
            'compare',
            'weight',
            'barcode',
        ]}),
    ]

    list_display = [
        'product',
        'color',
        'size',
        'type',
        'sku'
    ]

    list_filter = [
        'type'
    ]

    search_fields = [
        'shopifyId',
        'product',
        'color',
        'size',
        'type',
        'mpn',
        'sku',
        'barcode',
    ]


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    fields = [
        'variant',
        'url',
        'position'
    ]

    list_display = [
        'variant',
        'url',
        'position'
    ]

    list_filter = [
        'position'
    ]

    search_fields = [
        'variant',
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
