import environ
import tqdm
from concurrent.futures import ThreadPoolExecutor
from django.db import transaction

from vendor.models import Product, Sync, Type, Manufacturer, Tag

from utils import debug, common, shopify, const

env = environ.Env()


class DatabaseManager:
    def __init__(self, brand, Feed):
        self.brand = brand
        self.Feed = Feed

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def writeFeed(self, feeds: list):
        self.Feed.objects.all().delete()

        total = len(feeds)
        success = 0
        failed = 0
        for feed in feeds:
            try:
                self.Feed.objects.create(
                    mpn=feed.get('mpn'),
                    sku=feed.get('sku'),
                    pattern=feed.get('pattern'),
                    color=feed.get('color'),
                    name=feed.get('name', ""),

                    brand=feed.get('brand'),
                    type=feed.get('type'),
                    manufacturer=feed.get('manufacturer'),
                    collection=feed.get('collection', ""),

                    description=feed.get('description', ""),
                    usage=feed.get('usage', ""),
                    disclaimer=feed.get('disclaimer', ""),
                    width=feed.get('width', 0),
                    length=feed.get('length', 0),
                    height=feed.get('height', 0),
                    size=feed.get('size', ""),
                    repeatH=feed.get('repeatH', 0),
                    repeatV=feed.get('repeatV', 0),
                    specs=feed.get('specs', []),

                    yardsPR=feed.get('yardsPR', 0),
                    content=feed.get('content', ""),
                    match=feed.get('match', ""),
                    material=feed.get('material', ""),
                    finish=feed.get('finish', ""),
                    care=feed.get('care', ""),
                    weight=feed.get('weight', 5),
                    country=feed.get('country', ""),
                    upc=feed.get('upc', ""),
                    features=feed.get('features', []),

                    cost=feed.get('cost'),
                    msrp=feed.get('msrp', 0),
                    map=feed.get('map', 0),

                    uom=feed.get('uom'),
                    minimum=feed.get('minimum', 1),
                    increment=feed.get('increment', 1),

                    keywords=feed.get('keywords', ""),
                    colors=feed.get('colors', ""),

                    statusP=feed.get('statusP', False),
                    statusS=feed.get('statusS', False),
                    european=feed.get('european', False),
                    outlet=feed.get('outlet', False),
                    whiteGlove=feed.get('whiteGlove', False),
                    quickShip=feed.get('quickShip', False),
                    bestSeller=feed.get('bestSeller', False),

                    stockP=feed.get('stockP', 0),
                    stockS=feed.get('stockS', 0),
                    stockNote=feed.get('stockNote', ""),

                    thumbnail=feed.get('thumbnail', ""),
                    roomsets=feed.get('roomsets', []),

                    custom=feed.get('custom', {}),
                )
                success += 1
                debug.log(self.brand, f"Imported MPN: {feed.get('mpn')}")
            except Exception as e:
                failed += 1
                debug.warn(self.brand, str(e))
                continue

        debug.log(self.brand,
                  f"Finished writing {self.brand} feeds. Total: {total}, Success: {success}, Failed: {failed}")

    def validateFeed(self):

        # Validate Required fields
        invalidProducts = []

        products = self.Feed.objects.all()
        for product in products:
            if not (product.pattern and product.color and product.type and product.cost > 0 and product.uom):
                invalidProducts.append(product.mpn)

        if len(invalidProducts) == 0:
            debug.log(self.brand, "Product fields are ok!")
        else:
            debug.warn(
                self.brand, f"The following products missing mandatory fields: {', '.join(invalidProducts)}")

        # Validate Types
        unknownTypes = []

        types = self.Feed.objects.values_list('type', flat=True).distinct()
        for type in types:
            try:
                Type.objects.get(name=type)
            except Type.DoesNotExist:
                unknownTypes.append(type)

        if len(unknownTypes) == 0:
            debug.log(self.brand, "Types are ok!")
        else:
            debug.warn(self.brand, f"Unknown Types: {', '.join(unknownTypes)}")

        # Validate Manufacturers
        unknownManufacturers = []

        manufacturers = self.Feed.objects.values_list(
            'manufacturer', flat=True).distinct()
        for manufacturer in manufacturers:
            try:
                Manufacturer.objects.get(name=manufacturer)
            except Manufacturer.DoesNotExist:
                unknownManufacturers.append(manufacturer)

        if len(unknownManufacturers) == 0:
            debug.log(self.brand, "Manufacturers are ok!")
        else:
            debug.warn(
                self.brand, f"Unknown Manufacturers: {', '.join(unknownManufacturers)}")

        # Validate UOMs
        unknownUOMs = []

        uoms = self.Feed.objects.values_list('uom', flat=True).distinct()
        for uom in uoms:
            if uom not in ['Roll', 'Yard', 'Item', 'Panel', 'Square Foot', 'Set', 'Tile']:
                unknownUOMs.append(uom)

        if len(unknownUOMs) == 0:
            debug.log(self.brand, "UOMs are ok!")
        else:
            debug.warn(self.brand, f"Unknown UOMs: {', '.join(unknownUOMs)}")

    def statusSync(self, fullSync=False):
        products = Product.objects.filter(manufacturer__brand=self.brand)

        for product in products:
            try:
                feed = self.Feed.objects.get(sku=product.sku)

                feed.productId = product.shopifyId
                feed.save()

                if product.published != feed.statusP:
                    product.published = feed.statusP
                    product.save()

                    Sync.objects.get_or_create(
                        productId=product.shopifyId, type="Status")
                    debug.log(
                        self.brand, f"Changed Product: {product.sku} Status to: {feed.statusP}")

            except self.Feed.DoesNotExist:
                if product.published:
                    product.published = False
                    product.save()

                    Sync.objects.get_or_create(
                        productId=product.shopifyId, type="Status")
                    debug.log(
                        self.brand, f"Changed Product: {product.sku} Status to: False")

            if fullSync:
                Sync.objects.get_or_create(
                    productId=product.shopifyId, type="Status")
                debug.log(
                    self.brand, f"Resync Product: {product.sku} Status to: {product.published}")

    def contentSync(self):
        attributes = [
            "pattern",
            "color",
            "collection",
            "description",
            "width",
            "length",
            "height",
            "repeatH",
            "repeatV",
            "specs",
            "yardsPR",
            "content",
            "match",
            "material",
            "finish",
            "care",
            "country",
            "features",
            "usage",
            "disclaimer",
        ]

        feeds = self.Feed.objects.all()
        for feed in feeds:
            try:
                product = Product.objects.get(sku=feed.sku)
            except Product.DoesNotExist:
                continue

            if all(getattr(feed, attr) == getattr(product, attr) for attr in attributes):
                continue
            else:
                Sync.objects.get_or_create(
                    productId=product.shopifyId, type="Content")

    def priceSync(self):
        pass

    def tagSync(self):
        feeds = self.Feed.objects.all()
        for feed in tqdm(feeds, desc="Processing"):
            try:
                product = Product.objects.get(sku=feed.sku)
            except Product.DoesNotExist:
                continue

            newTags = set(self.generateTags(feed=feed, price=product.consumer))
            currentTags = set(product.tags.all())

            if newTags != currentTags:
                Sync.objects.get_or_create(
                    productId=product.shopifyId, type="Tag")

    def addProducts(self):
        pass

    def syncProduct(self, feed, product, private):
        manufacturer_name = "DecoratorsBest" if private else product.manufacturer
        title = f"{manufacturer_name} {product.name or f'{product.pattern} {product.color} {product.type}'}"

        manufacturer, type = (
            Manufacturer.objects.get(name=feed.manufacturer),
            Type.objects.get(name=feed.type),
        )

        feed_to_product_attrs = {
            'mpn': 'mpn', 'pattern': 'pattern', 'color': 'color',
            'collection': 'collection', 'description': 'description', 'width': 'width',
            'length': 'length', 'height': 'height', 'size': 'size', 'repeatH': 'repeatH',
            'repeatV': 'repeatV', 'specs': 'specs', 'uom': 'uom', 'minimum': 'minimum',
            'increment': 'increment', 'yardsPR': 'yardsPR', 'content': 'content',
            'match': 'match', 'material': 'material', 'finish': 'finish', 'care': 'care',
            'country': 'country', 'features': 'features', 'usage': 'usage',
            'disclaimer': 'disclaimer', 'cost': 'cost', 'weight': 'weight', 'barcode': 'upc',
        }

        for product_attr, feed_attr in feed_to_product_attrs.items():
            setattr(product, product_attr, getattr(feed, feed_attr))

        product.title = title
        product.manufacturer = manufacturer
        product.type = type

        with transaction.atomic():
            product.save()

    def updateProducts(self, feeds: list, private=False):
        total = len(feeds)

        def updateProduct(feed, index):
            try:
                product = Product.objects.get(sku=feed.sku)
            except Product.DoesNotExist:
                return

            tags = self.generateTags(feed=feed, price=product.consumer)
            for tag in tags:
                product.tags.add(tag)

            shopifyManager = shopify.ShopifyManager(
                product=product, thread=index)

            handle = shopifyManager.updateProduct()

            if handle:
                product.shopifyHandle = handle
                product.save()
                debug.log(
                    self.brand, f"Updated Product {product.sku} -- (Progress: {index}/{total})")

        with ThreadPoolExecutor(max_workers=20) as executor:
            for index, feed in enumerate(feeds):
                executor.submit(updateProduct, feed, index)

    def downloadImages(self):
        pass

    def generateTags(self, feed, price):
        tags = []

        # Generate Style tags
        allStyles = Tag.objects.filter(
            type="Style").values_list('name', flat=True)

        for style in allStyles:
            if style.lower() in feed.keywords.lower():
                try:
                    tag = Tag.objects.get(name=style, type="Style")
                    tags.append(tag)
                except Tag.DoesNotExist:
                    continue

        # Generate Category tags
        allCategories = Tag.objects.filter(
            type="Category").values_list('name', flat=True)

        for category in allCategories:
            if category.lower() in feed.keywords.lower():
                try:
                    tag = Tag.objects.get(name=category, type="Category")
                    tags.append(tag)
                except Tag.DoesNotExist:
                    continue

        # Generate Color tags
        for key, color in const.colorDict.items():
            if key.lower() in feed.colors.lower():
                try:
                    tag = Tag.objects.get(name=color, type="Color")
                    tags.append(tag)
                except Tag.DoesNotExist:
                    continue

        # Generate Size tags
        for key, size in const.sizeDict.items():
            sizeString = f"{feed.size.replace('W', '').replace('H', '').lower()} {common.toInt(feed.width / 12)}' x {common.toInt(feed.length / 12)}'"
            if key.lower() in sizeString:
                try:
                    tag = Tag.objects.get(name=size, type="Size")
                    tags.append(tag)
                except Tag.DoesNotExist:
                    continue

        # Generate Content tags
        allContents = Tag.objects.filter(
            type="Content").values_list('name', flat=True)

        for content in allContents:
            if content.lower() in feed.keywords.lower():
                try:
                    tag = Tag.objects.get(name=content, type="Content")
                    tags.append(tag)
                except Tag.DoesNotExist:
                    continue

        # Generate Designer tags
        allDesigners = Tag.objects.filter(
            type="Designer").values_list('name', flat=True)

        for designer in allDesigners:
            if designer.lower() in feed.collection.lower():
                try:
                    tag = Tag.objects.get(name=designer, type="Designer")
                    tags.append(tag)
                except Tag.DoesNotExist:
                    continue

        # Generate Shape tags
        allShapes = Tag.objects.filter(
            type="Shape").values_list('name', flat=True)

        for shape in allShapes:
            if shape.lower() in feed.collection.lower():
                try:
                    tag = Tag.objects.get(name=shape, type="Shape")
                    tags.append(tag)
                except Tag.DoesNotExist:
                    continue

        # Generate Price tag
        price_ranges = [
            (0, 25),
            (25, 50),
            (50, 100),
            (100, 200),
            (200, 300),
            (300, 400),
            (400, 500)
        ]

        for start, end in price_ranges:
            if start <= price < end:
                try:
                    tag = Tag.objects.get(
                        name=f"${start} - ${end}", type="Price")
                    tags.append(tag)
                except Tag.DoesNotExist:
                    continue

        else:
            if price >= 500:
                try:
                    tag = Tag.objects.get(name="$500 & Up", type="Price")
                    tags.append(tag)
                except Tag.DoesNotExist:
                    pass

        # Generate Group tags
        allGroups = {
            'statusS': "No Sample",
            'european': "European",
            'quickShip': "Quick Ship",
            'whiteGlove': "White Glove",
            'bestSeller': "Best Selling",
            'outlet': "Outlet"
        }

        for attr, tagName in allGroups.items():
            if getattr(feed, attr, False) or (attr == "statusS" and not getattr(feed, attr, True)):
                try:
                    tag = Tag.objects.get(name=tagName, type="Group")
                    tags.append(tag)
                except Tag.DoesNotExist:
                    pass

        return tags
