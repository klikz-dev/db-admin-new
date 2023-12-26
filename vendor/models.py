from django.db import models

VARIANT_TYPES = [
    ("Consumer", "Consumer"),
    ("Trade", "Trade"),
    ("Sample", "Sample"),
    ("Free Sample", "Free Sample"),
]

SYNC_TYPES = [
    ("Product", "Product"),
    ("Price", "Price"),
    ("Tag", "Tag"),
    ("Status", "Status"),
]


class Manufacturer(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    brand = models.CharField(max_length=200, blank=False, null=False)
    private = models.BooleanField(default=False)

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
    mpn = models.CharField(max_length=200, blank=False, null=False)
    sku = models.CharField(max_length=200, primary_key=True)

    shopifyId = models.CharField(max_length=200, blank=False, null=False)
    shopifyHandle = models.CharField(
        max_length=200, default=None, blank=True, null=True)

    title = models.CharField(max_length=200, blank=False, null=False)

    # Data
    pattern = models.CharField(max_length=200, null=False, blank=False)
    color = models.CharField(max_length=200, null=False, blank=False)

    manufacturer = models.ForeignKey(
        Manufacturer, related_name="products", on_delete=models.CASCADE, blank=False, null=False)
    type = models.ForeignKey(
        Type, related_name="products", on_delete=models.CASCADE, blank=False, null=False)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=2000, default=None, blank=True, null=True)
    width = models.FloatField(default=0, null=True, blank=True)
    length = models.FloatField(default=0, null=True, blank=True)
    height = models.FloatField(default=0, null=True, blank=True)
    repeatH = models.FloatField(default=0, null=True, blank=True)
    repeatV = models.FloatField(default=0, null=True, blank=True)
    specs = models.JSONField(default=None, null=True, blank=True)

    yardsPR = models.FloatField(default=0, null=True, blank=True)
    content = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    match = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    material = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    finish = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    care = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    country = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    features = models.JSONField(default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    disclaimer = models.CharField(
        max_length=2000, default=None, null=True, blank=True)
    upc = models.CharField(max_length=200, default=None, null=True, blank=True)

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
    compare = models.FloatField(default=0)

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
    hires = models.BooleanField(default=False)

    def __str__(self):
        return self.product


class Sync(models.Model):
    productId = models.CharField(max_length=200, blank=False, null=False)
    type = models.CharField(
        max_length=200, choices=SYNC_TYPES, default="Product")

    def __str__(self):
        return self.productId
