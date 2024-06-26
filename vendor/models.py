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

ORDER_TYPES = [
    ("Order", "Order"),
    ("Sample", "Sample"),
    ("Order/Sample", "Order/Sample"),
]


class Manufacturer(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    brand = models.CharField(max_length=200, blank=False, null=False)
    private = models.BooleanField(default=False)

    def productsCount(self):
        return self.products.count()

    def __str__(self):
        return self.name


class Type(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    parent = models.CharField(max_length=200, blank=True, null=True)

    def productsCount(self):
        return self.products.count()

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    type = models.CharField(max_length=200, blank=True, null=True)

    def productsCount(self):
        return self.products.count()

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

    cost = models.FloatField(default=5, null=False, blank=False)
    consumer = models.FloatField(default=19.99, null=False, blank=False)
    trade = models.FloatField(default=16.99, null=False, blank=False)
    sample = models.FloatField(default=5, null=False, blank=False)
    compare = models.FloatField(default=None, blank=True, null=True)

    weight = models.FloatField(default=1, null=True, blank=True)
    upc = models.CharField(
        max_length=200, default=None, blank=True, null=True)

    # Status
    published = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Image(models.Model):
    shopifyId = models.CharField(max_length=200, primary_key=True)

    url = models.URLField(max_length=1000, blank=False, null=False)
    position = models.IntegerField(default=1)

    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE, blank=False, null=False)

    hires = models.BooleanField(default=False)

    def __str__(self):
        return self.product.title


class Sync(models.Model):
    productId = models.CharField(max_length=200, blank=False, null=False)
    type = models.CharField(
        max_length=200, choices=SYNC_TYPES, default="Product")

    def __str__(self):
        return self.productId


class Inventory(models.Model):
    sku = models.CharField(max_length=200, primary_key=True)
    quantity = models.IntegerField(default=0)
    type = models.IntegerField(choices=STOCK_TYPES, default=1)
    note = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    brand = models.CharField(max_length=200, blank=False, null=False)

    def __str__(self):
        return self.sku


class Customer(models.Model):

    shopifyId = models.CharField(max_length=200, primary_key=True)

    email = models.CharField(
        max_length=200, unique=True, null=False, blank=False)

    firstName = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    lastName = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    company = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    address1 = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    address2 = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    city = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    state = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    zip = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    country = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    phone = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    note = models.TextField(
        max_length=2000, default=None, null=True, blank=True)
    tags = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.firstName} {self.lastName}"


class Order(models.Model):
    shopifyId = models.CharField(max_length=200, primary_key=True)

    po = models.CharField(max_length=200, unique=True, null=False, blank=False)

    orderType = models.CharField(
        max_length=200, default="Order", choices=ORDER_TYPES, blank=False, null=False)

    email = models.CharField(max_length=200, null=False, blank=False)
    phone = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    customer = models.ForeignKey(
        Customer, related_name='orders', on_delete=models.CASCADE, blank=False, null=False)

    shippingFirstName = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    shippingLastName = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    shippingCompany = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    shippingAddress1 = models.CharField(
        max_length=200, null=False, blank=False)
    shippingAddress2 = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    shippingCity = models.CharField(
        max_length=200, null=False, blank=False)
    shippingState = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    shippingZip = models.CharField(
        max_length=200, null=False, blank=False)
    shippingCountry = models.CharField(
        max_length=200, null=False, blank=False)
    shippingPhone = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    billingFirstName = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    billingLastName = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    billingCompany = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    billingAddress1 = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    billingAddress2 = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    billingCity = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    billingState = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    billingZip = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    billingCountry = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    billingPhone = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    subTotal = models.FloatField(default=0, null=False, blank=False)
    discount = models.FloatField(default=0, null=False, blank=False)
    shippingCost = models.FloatField(default=0, null=False, blank=False)
    tax = models.FloatField(default=0, null=False, blank=False)
    total = models.FloatField(default=0, null=False, blank=False)

    shippingMethod = models.CharField(max_length=200, null=False, blank=False)

    weight = models.FloatField(default=1, null=False, blank=False)
    orderDate = models.DateTimeField()

    status = models.CharField(
        max_length=200, default="New", null=False, blank=False)
    reference = models.TextField(
        max_length=2000, default=None, null=True, blank=True)

    internalNote = models.CharField(
        max_length=2000, default=None, null=True, blank=True)
    customerNote = models.CharField(
        max_length=2000, default=None, null=True, blank=True)

    manufacturers = models.JSONField(default=None, null=True, blank=True)

    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.po


class LineItem(models.Model):
    order = models.ForeignKey(
        Order, related_name='lineItems', on_delete=models.CASCADE, blank=False, null=False)

    product = models.ForeignKey(
        Product, related_name='lineItems', on_delete=models.CASCADE, blank=False, null=False)

    variant = models.CharField(
        max_length=200, choices=VARIANT_TYPES, default="Consumer")

    quantity = models.IntegerField(default=1, null=False, blank=False)

    orderPrice = models.FloatField(default=0, null=False, blank=False)
    orderDiscount = models.FloatField(default=0, null=False, blank=False)
    orderWeight = models.FloatField(default=0, null=False, blank=False)

    backorder = models.DateField(default=None, null=True, blank=True)

    def __str__(self):
        return self.order.po


class Tracking(models.Model):
    order = models.ForeignKey(
        Order, related_name='trackings', on_delete=models.CASCADE, blank=False, null=False)

    brand = models.CharField(max_length=200, null=False, blank=False)

    company = models.CharField(
        max_length=200, default="UPS", null=False, blank=False)
    number = models.CharField(max_length=200, null=False, blank=False)

    def __str__(self):
        return self.number


class Roomvo(models.Model):
    sku = models.CharField(max_length=200, primary_key=True)
    name = models.CharField(
        max_length=200, null=False, blank=False)
    availability = models.CharField(
        max_length=20, default="Yes", null=False, blank=False)

    width = models.CharField(
        max_length=200, null=False, blank=False)
    length = models.CharField(
        max_length=200, null=False, blank=False)
    thickness = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    dimension_display = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    horizontal_repeat = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    vertical_repeat = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    layout = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, null=False, blank=False)
    product_type = models.CharField(
        max_length=200, null=False, blank=False)

    filter_category = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    filter_style = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    filter_color = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    filter_subtype = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    image = models.CharField(
        max_length=200, null=False, blank=False)
    link = models.CharField(
        max_length=200, null=False, blank=False)

    cart_id = models.CharField(
        max_length=200, null=False, blank=False)
    cart_id_trade = models.CharField(
        max_length=200, null=False, blank=False)
    cart_id_sample = models.CharField(
        max_length=200, null=False, blank=False)
    cart_id_free_sample = models.CharField(
        max_length=200, null=False, blank=False)

    def __str__(self):
        return self.sku
