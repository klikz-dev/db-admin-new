import environ

from utils import debug, const

env = environ.Env()

log, warn, error = debug.log, debug.warn, debug.error


class FeedManager:
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
                    depth=product.get('depth', 0),
                    size=product.get('size', ""),
                    dimension=product.get('dimension', ""),
                    repeatH=product.get('repeatH', 0),
                    repeatV=product.get('repeatV', 0),
                    repeat=product.get('repeat', ""),

                    yards=product.get('yards', 0),
                    content=product.get('content', ""),
                    match=product.get('match', ""),
                    material=product.get('material', ""),
                    finish=product.get('finish', ""),
                    care=product.get('care', ""),
                    construction=product.get('construction', ""),
                    specs=product.get('specs', []),
                    features=product.get('features', []),
                    weight=product.get('weight', 5),
                    country=product.get('country', ""),
                    upc=product.get('upc', ""),
                    custom=product.get('custom', {}),

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
                    roomsets=product.get('roomsets', [])
                )
                success += 1
                log(feed.brand, f"Imported MPN: {feed.mpn}")
            except Exception as e:
                failed += 1
                warn(self.brand, str(e))
                continue

        log(self.brand,
            f"Finished writing {self.brand} feeds. Total: {total}, Success: {success}, Failed: {failed}")
