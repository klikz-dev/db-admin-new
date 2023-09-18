from django.contrib import admin

from .models import Manufacturer, Type, Tag, Product, Variant, Image


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    fields = [
        'name',
        'brand'
    ]

    list_display = [
        'name',
        'brand'
    ]

    list_filter = [
        'brand'
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
            'data',
        ]}),
        ('Category', {'fields': [
            'manufacturer',
            'type',
            'tags',
        ]}),
        (None, {'fields': [
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
        'manufacturer',
        'type',
        'published'
    ]

    search_fields = [
        'mpn',
        'sku',
        'title',
        'description',
        'tags'
    ]


@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Main', {'fields': [
            'shopifyId',
            'product',
            'type',
        ]}),
        ('Information', {'fields': [
            'cost',
            'price',
            'weight',
            'barcode',
        ]}),
    ]

    list_display = [
        'shopifyId',
        'product',
        'type',
        'cost',
        'price',
    ]

    list_filter = [
        'type',
    ]

    search_fields = [
        'shopifyId',
        'product',
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
