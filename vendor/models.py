from django.db import models

VARIANT_TYPES = [
    ("Consumer", "Consumer"),
    ("Trade", "Trade"),
    ("Sample", "Sample"),
    ("Free Sample", "Free Sample"),
]


class Manufacturer(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    brand = models.CharField(max_length=200, blank=False, null=False)

    def __str__(self):
        return self.name


class Type(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    parent = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    type = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    sku = models.CharField(max_length=200, primary_key=True)
    mpn = models.CharField(max_length=200, blank=False, null=False)

    shopifyId = models.CharField(max_length=200, blank=False, null=False)
    shopifyHandle = models.CharField(
        max_length=200, default=None, blank=True, null=True)

    title = models.CharField(max_length=200, blank=False, null=False)
    description = models.CharField(
        max_length=2000, default=None, blank=True, null=True)
    data = models.JSONField()

    manufacturer = models.ForeignKey(
        Manufacturer, related_name="products", on_delete=models.CASCADE, blank=False, null=False)
    type = models.ForeignKey(
        Type, related_name="products", on_delete=models.CASCADE, blank=False, null=False)
    tags = models.ManyToManyField(Tag, related_name="products")

    published = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Variant(models.Model):
    shopifyId = models.CharField(max_length=200, primary_key=True)

    product = models.ForeignKey(
        Product, related_name="variants", on_delete=models.CASCADE, blank=False, null=False)

    type = models.CharField(
        max_length=200, choices=VARIANT_TYPES, default="Consumer")

    cost = models.FloatField(default=0)
    price = models.FloatField(default=0)

    weight = models.FloatField(default=0)
    barcode = models.CharField(
        max_length=200, default=None, blank=True, null=True)

    def __str__(self):
        return f"{self.type} - {self.product}"


class Image(models.Model):
    url = models.URLField(primary_key=True)
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE, blank=False, null=False)
    position = models.IntegerField(default=1)

    def __str__(self):
        return self.product
