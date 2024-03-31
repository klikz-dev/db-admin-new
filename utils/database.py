import environ
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from django.db import transaction

from vendor.models import Product, Sync, Type, Manufacturer, Tag, Inventory

from utils import debug, common, shopify, const

env = environ.Env()


ATTR_DICT = [
    'pattern',
    'color',
    'collection',
    'description',
    'width',
    'length',
    'height',
    'size',
    'repeatH',
    'repeatV',
    'uom',
    'minimum',
    'increment',
    'yardsPR',
    'content',
    'match',
    'material',
    'finish',
    'care',
    'weight',
    'country',
    'specs',
    'features',
    'usage',
    'disclaimer',
]


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
        for feed in tqdm(feeds):
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
                # debug.log(self.brand, f"Imported MPN: {feed.get('mpn')}")
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
            if uom not in ['Roll', 'Double Roll', 'Yard', 'Each', 'Item', 'Panel', 'Square Foot', 'Set', 'Tile', 'Spool', 'Meter']:
                unknownUOMs.append(uom)

        if len(unknownUOMs) == 0:
            debug.log(self.brand, "UOMs are ok!")
        else:
            debug.warn(self.brand, f"Unknown UOMs: {', '.join(unknownUOMs)}")

    def statusSync(self, fullSync=False):
        products = Product.objects.filter(manufacturer__brand=self.brand)

        for product in tqdm(products):
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

    def contentSync(self, private=False):
        feeds = self.Feed.objects.all()
        for feed in tqdm(feeds):
            try:
                product = Product.objects.get(sku=feed.sku)
            except Product.DoesNotExist:
                continue

            title = f"{'DecoratorsBest' if private else feed.manufacturer} {feed.name}"

            if any(getattr(feed, attr) != getattr(product, attr) for attr in ATTR_DICT):
                for attr in ATTR_DICT:
                    setattr(product, attr, getattr(feed, attr))
            elif feed.manufacturer != product.manufacturer.name:
                product.manufacturer = Manufacturer.objects.get(
                    name=feed.manufacturer)
            elif feed.type != product.type.name:
                product.type = Type.objects.get(name=feed.type)
            elif title != product.title:
                product.title = title
            else:
                continue

            product.save()

            Sync.objects.get_or_create(
                productId=product.shopifyId, type="Content")

    def priceSync(self):
        feeds = self.Feed.objects.all()
        for feed in tqdm(feeds):
            try:
                product = Product.objects.get(sku=feed.sku)
            except Product.DoesNotExist:
                continue

            markup = const.markup[self.brand]
            if feed.type in markup:
                markup = markup[feed.type]
            if feed.european and "European" in markup:
                markup = markup["European"]

            cost = feed.cost
            map = feed.map
            consumer = common.toPrice(cost, markup['consumer'])
            trade = common.toPrice(cost, markup['trade'])

            consumer = map if map > 0 else consumer

            if consumer < 20:
                consumer = 19.99
            if trade < 17:
                trade = 16.99

            if cost == product.cost and consumer == product.consumer and trade == product.trade:
                continue
            else:
                product.cost = cost
                product.consumer = consumer
                product.trade = trade
                product.save()

                Sync.objects.get_or_create(
                    productId=product.shopifyId, type="Price")

    def tagSync(self):
        feeds = self.Feed.objects.all()
        for feed in tqdm(feeds):
            try:
                product = Product.objects.get(sku=feed.sku)
            except Product.DoesNotExist:
                continue

            newTags = set(self.generateTags(feed=feed, price=product.consumer))
            currentTags = set(product.tags.all())

            if newTags != currentTags:
                product.tags.clear()
                product.tags.add(*newTags)

                Sync.objects.get_or_create(
                    productId=product.shopifyId, type="Tag")

    def updateInventory(self, stocks, type=1, reset=True):
        if reset:
            Inventory.objects.filter(brand=self.brand).delete()

        for stock in stocks:
            if not stock['sku']:
                continue

            try:
                Inventory.objects.update_or_create(
                    sku=stock['sku'],
                    quantity=stock['quantity'],
                    type=type,
                    note=stock['note'],
                    brand=self.brand
                )

                debug.log(
                    self.brand, f"Update Inventory. {stock['sku']} : {stock['quantity']}")

            except Exception as e:
                debug.warn(self.brand, str(e))

    def generateTags(self, feed, price):
        tags = []

        # Generate Style tags
        allStyles = Tag.objects.filter(
            type="Style").values_list('name', flat=True)

        for style in allStyles:
            if style.lower() in common.toText(feed.keywords).lower():
                try:
                    tag = Tag.objects.get(name=style, type="Style")
                    tags.append(tag)
                except Tag.DoesNotExist:
                    continue

        # Generate Category tags
        allCategories = Tag.objects.filter(
            type="Category").values_list('name', flat=True)

        for category in allCategories:
            if category.lower() in common.toText(feed.keywords).lower():
                try:
                    tag = Tag.objects.get(name=category, type="Category")
                    tags.append(tag)
                except Tag.DoesNotExist:
                    continue

        # Generate Color tags
        for key, color in const.colorDict.items():
            if key.lower() in common.toText(feed.colors).lower():
                try:
                    tag = Tag.objects.get(name=color, type="Color")
                    tags.append(tag)
                except Tag.DoesNotExist:
                    continue

        # Generate Size tags
        sizes = []
        lumbar = True

        for key, size in const.sizeDict.items():
            sizeString = f"{feed.size.replace('W', '').replace('H', '').lower()} {common.toInt(feed.width / 12)}' x {common.toInt(feed.length / 12)}'"
            if key.lower() in sizeString:
                sizes.append(size)
                lumbar = False

        if feed.type == "Pillow" and lumbar:
            sizes.append("Lumbar")

        if feed.type == "Trim" and feed.width > 0:
            if feed.width < 1:
                sizes.append('Up to 1"')
            elif feed.width < 2:
                sizes.append('1" to 2"')
            elif feed.width < 3:
                sizes.append('2" to 3"')
            elif feed.width < 4:
                sizes.append('3" to 4"')
            elif feed.width < 5:
                sizes.append('4" to 5"')
            else:
                sizes.append('5" and More')

        for size in sizes:
            try:
                tag = Tag.objects.get(name=size, type="Size")
                tags.append(tag)
            except Tag.DoesNotExist:
                continue

        # Generate Content tags
        allContents = Tag.objects.filter(
            type="Content").values_list('name', flat=True)

        for content in allContents:
            if content.lower() in common.toText(feed.keywords).lower():
                try:
                    tag = Tag.objects.get(name=content, type="Content")
                    tags.append(tag)
                except Tag.DoesNotExist:
                    continue

        # Generate Designer tags
        allDesigners = Tag.objects.filter(
            type="Designer").values_list('name', flat=True)

        for designer in allDesigners:
            if designer.lower() in common.toText(feed.collection).lower():
                try:
                    tag = Tag.objects.get(name=designer, type="Designer")
                    tags.append(tag)
                except Tag.DoesNotExist:
                    continue

        # Generate Shape tags
        allShapes = Tag.objects.filter(
            type="Shape").values_list('name', flat=True)

        for shape in allShapes:
            if shape.lower() in common.toText(feed.collection).lower():
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
            if (attr != "statusS" and getattr(feed, attr, False)) or (attr == "statusS" and not getattr(feed, attr, True)):
                try:
                    tag = Tag.objects.get(name=tagName, type="Group")
                    tags.append(tag)
                except Tag.DoesNotExist:
                    pass

        return tags
