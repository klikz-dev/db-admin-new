import environ

from vendor.models import Product, Sync, Type, Manufacturer

from utils import debug

env = environ.Env()


class DatabaseManager:
    def __init__(self, brand, Feed):
        self.brand = brand
        self.Feed = Feed

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def writeFeed(self, products: list):
        self.Feed.objects.all().delete()

        total = len(products)
        success = 0
        failed = 0
        for product in products:
            try:
                feed = self.Feed.objects.create(
                    mpn=product.get('mpn'),
                    sku=product.get('sku'),
                    pattern=product.get('pattern'),
                    color=product.get('color'),
                    name=product.get('name', ""),

                    brand=product.get('brand'),
                    type=product.get('type'),
                    manufacturer=product.get('manufacturer'),
                    collection=product.get('collection', ""),

                    description=product.get('description', ""),
                    usage=product.get('usage', ""),
                    disclaimer=product.get('disclaimer', ""),
                    width=product.get('width', 0),
                    length=product.get('length', 0),
                    height=product.get('height', 0),
                    repeatH=product.get('repeatH', 0),
                    repeatV=product.get('repeatV', 0),
                    specs=product.get('specs', []),

                    yardsPR=product.get('yardsPR', 0),
                    content=product.get('content', ""),
                    match=product.get('match', ""),
                    material=product.get('material', ""),
                    finish=product.get('finish', ""),
                    care=product.get('care', ""),
                    weight=product.get('weight', 5),
                    country=product.get('country', ""),
                    upc=product.get('upc', ""),
                    features=product.get('features', []),

                    cost=product.get('cost'),
                    msrp=product.get('msrp', 0),
                    map=product.get('map', 0),

                    uom=product.get('uom'),
                    minimum=product.get('minimum', 1),
                    increment=product.get('increment', 1),

                    keywords=product.get('keywords', ""),
                    colors=product.get('colors', ""),

                    statusP=product.get('statusP', False),
                    statusS=product.get('statusS', False),
                    european=product.get('european', False),
                    outlet=product.get('outlet', False),
                    whiteGlove=product.get('whiteGlove', False),
                    quickShip=product.get('quickShip', False),
                    bestSeller=product.get('bestSeller', False),

                    stockP=product.get('stockP', 0),
                    stockS=product.get('stockS', 0),
                    stockNote=product.get('stockNote', ""),

                    thumbnail=product.get('thumbnail', ""),
                    roomsets=product.get('roomsets', []),

                    custom=product.get('custom', {}),
                )
                success += 1
                debug.log(self.brand, f"Imported MPN: {feed.mpn}")
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

    def updateProducts(self):
        pass

    def downloadImages(self):
        pass
