import os
import environ
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from vendor.models import Product, Sync, Type, Manufacturer, Tag, Inventory

from utils import debug, common, shopify, const

env = environ.Env()

IMAGEDIR = f"{os.path.expanduser('~')}/admin/vendor/management/files/images"

ATTR_DICT = [
    'mpn',
    'sku',
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
    'upc',
    'cost',
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
                    name=feed.get('name'),

                    brand=feed.get('brand'),
                    type=feed.get('type'),
                    manufacturer=feed.get('manufacturer'),
                    collection=feed.get('collection', ""),

                    description=feed.get('description', feed.get('name')),
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
                    weight=feed.get('weight', 1),
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
            if uom not in ['Roll', 'Yard', 'Each', 'Item', 'Panel', 'Square Foot', 'Set', 'Tile', 'Spool', 'Meter']:
                unknownUOMs.append(uom)

        if len(unknownUOMs) == 0:
            debug.log(self.brand, "UOMs are ok!")
        else:
            debug.warn(self.brand, f"Unknown UOMs: {', '.join(unknownUOMs)}")

    def addProducts(self, private=False):
        feeds = self.Feed.objects.filter(productId=None).filter(statusP=True)

        def createProduct(index, feed, private):
            try:
                Product.objects.get(sku=feed.sku)
                raise (f"{feed.sku} is already in Shopify.")
            except Product.DoesNotExist:
                product = Product(sku=feed.sku)

            # Copy Feed object to Product object temporarily
            if feed.brand == "Jamie Young" and feed.collection == "LIFESTYLE":
                private = True

            title = f"{'DecoratorsBest' if private else feed.manufacturer} {feed.name}"

            for attr in ATTR_DICT:
                setattr(product, attr, getattr(feed, attr))
            product.manufacturer = Manufacturer.objects.get(
                name=feed.manufacturer)
            product.type = Type.objects.get(name=feed.type)
            product.title = title

            consumer, trade, sample, _ = common.getPricing(feed)
            product.consumer = consumer
            product.trade = trade
            product.sample = sample

            # Upload to Shopify
            shopifyManager = shopify.ShopifyManager(
                product=product, thread=index)
            productData = shopifyManager.createProduct()

            # Save Shopify values back into Product object
            product.shopifyId = productData['id']
            product.shopifyHandle = productData['handle']

            for variant in productData['variants']:
                if variant['title'] == "Consumer":
                    product.consumerId = variant['id']
                elif variant['title'] == "Trade":
                    product.tradeId = variant['id']
                elif variant['title'] == "Sample":
                    product.sampleId = variant['id']
                elif variant['title'] == "Free Sample":
                    product.freeSampleId = variant['id']

            product.save()

            # Update Feed's shopifyId accordingly
            feed.productId = productData['id']
            feed.save()

        with ThreadPoolExecutor(max_workers=20) as executor:
            total = len(feeds)
            future_to_feed = {executor.submit(
                createProduct, index, feed, private): (index, feed) for index, feed in enumerate(feeds)}

            for future in as_completed(future_to_feed):
                index, feed = future_to_feed[future]

                try:
                    future.result()
                    debug.log(
                        self.brand, f"{index}/{total} - Product {feed.productId} has been created successfully.")
                except Exception as e:
                    debug.warn(
                        self.brand, f"{index}/{total} - Product Upload for {feed.sku} has been failed. {str(e)}")

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

    def contentSync(self, private=False, fullSync=False):
        feeds = self.Feed.objects.all()
        for feed in tqdm(feeds):
            try:
                product = Product.objects.get(sku=feed.sku)
            except Product.DoesNotExist:
                continue

            if feed.brand == "Jamie Young" and feed.collection == "LIFESTYLE":
                private = True

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
                if fullSync:
                    Sync.objects.get_or_create(
                        productId=product.shopifyId, type="Content")
                continue

            product.save()

            Sync.objects.get_or_create(
                productId=product.shopifyId, type="Content")

    def priceSync(self, fullSync=False):
        feeds = self.Feed.objects.all()
        for feed in tqdm(feeds):
            try:
                product = Product.objects.get(sku=feed.sku)
            except Product.DoesNotExist:
                continue

            consumer, trade, sample, compare = common.getPricing(feed)

            if feed.cost == product.cost and consumer == product.consumer and trade == product.trade and sample == product.sample and compare == product.compare:
                continue
            else:
                product.cost = feed.cost
                product.consumer = consumer
                product.trade = trade
                product.sample = sample
                product.compare = compare
                product.save()

                Sync.objects.get_or_create(
                    productId=product.shopifyId, type="Price")

            if fullSync:
                Sync.objects.get_or_create(
                    productId=product.shopifyId, type="Price")

    def tagSync(self, fullSync=False):
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

            if fullSync:
                Sync.objects.get_or_create(
                    productId=product.shopifyId, type="Tag")

    def downloadImages(self, fullSync=False):
        hasImageIds = Product.objects.filter(manufacturer__brand=self.brand).filter(
            images__position=1).values_list('shopifyId', flat=True).distinct()

        feeds = self.Feed.objects.exclude(productId=None)
        if not fullSync:
            feeds = feeds.exclude(productId__in=hasImageIds)

        def downloadImage(_, feed):
            thumbnail = feed.thumbnail
            roomsets = feed.roomsets

            if thumbnail:
                common.downloadFileFromLink(
                    src=thumbnail, dst=f"{IMAGEDIR}/thumbnail/{feed.productId}.jpg")

            for index, roomset in enumerate(roomsets):
                common.downloadFileFromLink(
                    src=roomset, dst=f"{IMAGEDIR}/roomset/{feed.productId}_{index + 2}.jpg")

        common.thread(rows=feeds, function=downloadImage)

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
            if common.wordInText(style, feed.keywords):
                try:
                    tag = Tag.objects.get(name=style, type="Style")
                    tags.append(tag)
                except Tag.DoesNotExist:
                    continue

        # Generate Category tags
        if feed.type in [
            "Fabric", "Upholstery Fabric", "Drapery Fabric",
            "Wallpaper", "Mural",
            "Pillow", "Pillow Kit", "Pillow Insert", "Pillow Cover", "Outdoor Pillow", "Decorative Pillow",
            "Trim",
            "Rug", "Rug Pad",
        ]:
            allCategories = Tag.objects.filter(
                type="Category").values_list('name', flat=True)

            for category in allCategories:
                categoryName = category.split(
                    ">")[1] if ">" in category else category
                if common.wordInText(categoryName, feed.keywords):
                    try:
                        tag = Tag.objects.get(name=category, type="Category")
                        tags.append(tag)
                    except Tag.DoesNotExist:
                        continue

        # Generate Color tags
        for key, color in const.colorDict.items():
            if common.wordInText(key, feed.colors):
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
            if common.wordInText(key, sizeString):
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
            if common.wordInText(content, feed.keywords):
                try:
                    tag = Tag.objects.get(name=content, type="Content")
                    tags.append(tag)
                except Tag.DoesNotExist:
                    continue

        # Generate Designer tags
        allDesigners = Tag.objects.filter(
            type="Designer").values_list('name', flat=True)

        for designer in allDesigners:
            if common.wordInText(designer, feed.collection):
                try:
                    tag = Tag.objects.get(name=designer, type="Designer")
                    tags.append(tag)
                except Tag.DoesNotExist:
                    continue

        # Generate Shape tags
        allShapes = Tag.objects.filter(
            type="Shape").values_list('name', flat=True)

        for shape in allShapes:
            if common.wordInText(shape, feed.collection):
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
