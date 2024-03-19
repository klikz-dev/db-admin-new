from django.db import models

VARIANT_TYPES = [
    ("Consumer", "Consumer"),
    ("Trade", "Trade"),
    ("Sample", "Sample"),
    ("Free Sample", "Free Sample"),
]

SYNC_TYPES = [
    ("Status", "Status"),
    ("Content", "Content"),
    ("Price", "Price"),
    ("Tag", "Tag"),
]

STOCK_TYPES = [
    (1, "Show Stock & Note"),
    (2, "Show Stock & Hide Stock Note"),
    (3, "Hide Stock & Show Note"),
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
    # Primary
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
    size = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    repeatH = models.FloatField(default=0, null=True, blank=True)
    repeatV = models.FloatField(default=0, null=True, blank=True)
    specs = models.JSONField(default=None, null=True, blank=True)

    uom = models.CharField(
        max_length=200, default="Item", null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.IntegerField(default=1)

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
        max_length=1000, default=None, null=True, blank=True)
    country = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    features = models.JSONField(default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    disclaimer = models.CharField(
        max_length=2000, default=None, null=True, blank=True)

    tags = models.ManyToManyField(Tag, related_name="products")

    # Variant
    consumerId = models.CharField(
        max_length=200, unique=True, db_index=True, null=False, blank=False)
    tradeId = models.CharField(
        max_length=200, unique=True, db_index=True, null=False, blank=False)
    sampleId = models.CharField(
        max_length=200, unique=True, db_index=True, null=False, blank=False)
    freeSampleId = models.CharField(
        max_length=200, unique=True, db_index=True, null=False, blank=False)

    cost = models.FloatField(default=0)
    consumer = models.FloatField(default=0)
    trade = models.FloatField(default=0)
    sample = models.FloatField(default=0)
    compare = models.FloatField(default=0, blank=True, null=True)

    weight = models.FloatField(default=0)
    barcode = models.CharField(
        max_length=200, default=None, blank=True, null=True)

    # Status
    published = models.BooleanField(default=True)

    def __str__(self):
        return self.title


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


class Inventory(models.Model):
    sku = models.CharField(max_length=200, primary_key=True)
    quantity = models.IntegerField(default=0)
    type = models.IntegerField(choices=SYNC_TYPES, default=1)
    note = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    brand = models.CharField(max_length=200, blank=False, null=False)

    def __str__(self):
        return self.sku
