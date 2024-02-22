import environ

from vendor.models import Product, Sync

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

    def statusSync(self, fullSync=False):
        products = Product.objects.filter(manufacturer__brand=self.brand)

        for product in products:
            try:
                feed = self.Feed.objects.get(sku=product.sku)

                if product.published != feed.statusP:
                    product.published = feed.statusP
                    product.save()

                    Sync.objects.get_or_create(
                        productId=product.productId, type="Status")
                    debug.log(
                        self.brand, f"Changed Product: {product.sku} Status to: {feed.statusP}")

            except self.Feed.DoesNotExist:
                if product.published:
                    product.published = False
                    product.save()

                    Sync.objects.get_or_create(
                        productId=product.productId, type="Status")
                    debug.log(
                        self.brand, f"Changed Product: {product.sku} Status to: False")

            if fullSync:
                Sync.objects.get_or_create(
                    productId=product.productId, type="Status")
                debug.log(
                    self.brand, f"Resync Product: {product.sku} Status to: {product.published}")
