import environ

from vendor.models import Product, Sync, Type, Manufacturer

from utils import debug, shopify

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
        pass

    def addProducts(self):
        pass

    def updateProducts(self, feeds: list):
        for feed in feeds:
            try:
                product = Product.objects.get(sku=feed.sku)
            except Product.DoesNotExist:
                continue

            handle = shopify.updateProduct(product=product)

            if handle:
                product.shopifyHandle = handle
                product.save()

                debug.log(self.brand, f"Updated Product {product.sku}")

    def downloadImages(self):
        pass
