from concurrent.futures import ThreadPoolExecutor
import requests
import json
import environ
from urllib.parse import quote

from django.core.management.base import BaseCommand

from utils import common, debug, shopify
from vendor.models import Type, Manufacturer, Tag, Product

from feed.models import Brewster
from feed.models import Couture
from feed.models import Covington
from feed.models import DanaGibson
from feed.models import ElaineSmith
from feed.models import ExquisiteRugs
from feed.models import Galerie
from feed.models import HubbardtonForge
from feed.models import JaipurLiving
from feed.models import JamieYoung
from feed.models import JFFabrics
from feed.models import Kasmir
from feed.models import Kravet
from feed.models import Materialworks
from feed.models import Maxwell
from feed.models import MindTheGap
from feed.models import NOIR
from feed.models import OliviaQuinn
from feed.models import PKaufmann
from feed.models import PeninsulaHome
from feed.models import PhillipJeffries
from feed.models import PhillipsCollection
from feed.models import Pindler
from feed.models import Poppy
from feed.models import Port68
from feed.models import PremierPrints
from feed.models import Scalamandre
from feed.models import Schumacher
from feed.models import Seabrook
from feed.models import Stout
from feed.models import Surya
from feed.models import Tempaper
from feed.models import York
from feed.models import Zoffany

env = environ.Env()

types = [
    ("Fabric", "Root"),
    ("Wallpaper", "Root"),
    ("Trim", "Root"),
    ("Rug", "Root"),
    ("Pillow", "Root"),
    ("Furniture", "Root"),
    ("Lighting", "Root"),
    ("Accent", "Root"),
    ("Mirror", "Root"),
    ("Wall Art", "Root"),
    ("Drapery Fabric", "Fabric"),
    ("Upholstery Fabric", "Fabric"),
    ("Mural", "Wallpaper"),
    ("Border", "Wallpaper"),
    ("Applique", "Trim"),
    ("Braid", "Trim"),
    ("Cord", "Trim"),
    ("Cord with Tape", "Trim"),
    ("Fringe", "Trim"),
    ("Gimp", "Trim"),
    ("Rosette", "Trim"),
    ("Tassel with Fringe", "Trim"),
    ("Tassel", "Trim"),
    ("Tieback", "Trim"),
    ("Rug Pad", "Rug"),
    ("Rectangle Throw Pillow", "Pillow"),
    ("Square Throw Pillow", "Pillow"),
    ("Pillow Cover", "Pillow"),
    ("Pillow Insert", "Pillow"),
    ("Pillow Kit", "Pillow"),
    ("Decorative Pillow", "Pillow"),
    ("Outdoor Pillow", "Pillow"),
    ("Bed", "Furniture"),
    ("Bench", "Furniture"),
    ("Bookcase", "Furniture"),
    ("Cabinet", "Furniture"),
    ("Chair", "Furniture"),
    ("Console", "Furniture"),
    ("Coffee Table", "Furniture"),
    ("Desk", "Furniture"),
    ("Sofa", "Furniture"),
    ("Side Table", "Furniture"),
    ("Ottoman", "Furniture"),
    ("Stool", "Furniture"),
    ("Bar Stool", "Furniture"),
    ("Counter Stool", "Furniture"),
    ("Dining Chair", "Furniture"),
    ("Accent Chair", "Furniture"),
    ("Accent Table", "Furniture"),
    ("Dresser", "Furniture"),
    ("End Table", "Furniture"),
    ("Garden Stool", "Furniture"),
    ("Dining Table", "Furniture"),
    ("Cocktail Table", "Furniture"),
    ("Hutch", "Furniture"),
    ("Chandelier", "Lighting"),
    ("Floor Lamp", "Lighting"),
    ("Table Lamp", "Lighting"),
    ("Wall Sconce", "Lighting"),
    ("Pendant", "Lighting"),
    ("Flush Mount", "Lighting"),
    ("Semi-Flush Mount", "Lighting"),
    ("Accent Lamp", "Lighting"),
    ("Lamp Shade", "Lighting"),
    ("Torchier", "Lighting"),
    ("Rectangle Mirror", "Mirror"),
    ("Round Mirror", "Mirror"),
    ("Square Mirror", "Mirror"),
    ("Accessory", "Accent"),
    ("Tabletop", "Accent"),
    ("Print", "Accent"),
    ("Plate", "Accent"),
    ("Bookend", "Accent"),
    ("Bowl", "Accent"),
    ("Box", "Accent"),
    ("Candlestick", "Accent"),
    ("Planter", "Accent"),
    ("Screen", "Accent"),
    ("Sculpture", "Accent"),
    ("Tray", "Accent"),
    ("Vase", "Accent"),
    ("Wastebasket", "Accent"),
    ("Throw", "Accent"),
    ("Basket", "Accent"),
    ("Candle Holder", "Accent"),
    ("Decorative Bowl", "Accent"),
    ("Hurricane", "Accent"),
    ("Object", "Accent"),
    ("Candleholder", "Accent"),
    ("Cachepot", "Accent"),
    ("Ginger Jar", "Accent"),
    ("Ice Bucket", "Accent"),
    ("Tote", "Accent"),
    ("Decorative Accent", "Accent"),
    ("Tissue Box", "Accent"),
    ("Pouf", "Accent"),
    ("Painting", "Wall Art"),
    ("Wall Hanging", "Wall Art"),
    ("Original Art", "Wall Art"),
    ("Wall Accent", "Wall Art"),
    ("Wall Mirror", "Wall Art"),
]

manufacturers = [
    ("Brewster Home Fashions", "Brewster", False),
    ("A-Street Prints", "Brewster", False),
    ("Couture", "Couture", False),
    ("Covington", "Covington", True),
    ("Dana Gibson", "Dana Gibson", False),
    ("Elaine Smith", "Elaine Smith", False),
    ("Exquisite Rugs", "Exquisite Rugs", False),
    ("Hubbardton Forge", "Hubbardton Forge", False),
    ("Jaipur Living", "Jaipur Living", False),
    ("Jamie Young", "Jamie Young", False),
    ("JF Fabrics", "JF Fabrics", False),
    ("Casadeco", "JF Fabrics", False),
    ("Caselio", "JF Fabrics", False),
    ("ILIV", "JF Fabrics", False),
    ("Kasmir", "Kasmir", False),
    ("Kravet", "Kravet", False),
    ("Andrew Martin", "Kravet", False),
    ("Baker Lifestyle", "Kravet", False),
    ("Brunschwig & Fils", "Kravet", False),
    ("Clarke & Clarke", "Kravet", False),
    ("Cole & Son", "Kravet", False),
    ("Donghia", "Kravet", False),
    ("G P & J Baker", "Kravet", False),
    ("Gaston Y Daniela", "Kravet", False),
    ("Lee Jofa", "Kravet", False),
    ("Lizzo", "Kravet", False),
    ("Mulberry", "Kravet", False),
    ("Threads", "Kravet", False),
    ("Winfield Thybony", "Kravet", False),
    ("Kravet Decor", "Kravet", False),
    ("Materialworks", "Materialworks", False),
    ("Maxwell", "Maxwell", False),
    ("MindTheGap", "MindTheGap", False),
    ("NOIR", "NOIR", False),
    ("Peninsula Home", "Peninsula Home", False),
    ("Phillip Jeffries", "Phillip Jeffries", False),
    ("Phillips Collection", "Phillips Collection", False),
    ("Pindler", "Pindler", False),
    ("Scalamandre Maison", "Port 68", False),
    ("Madcap Cottage Décor", "Port 68", False),
    ("Premier Prints", "Premier Prints", True),
    ("Scalamandre", "Scalamandre", False),
    ("Aldeco", "Scalamandre", False),
    ("Alhambra", "Scalamandre", False),
    ("Boris Kroll", "Scalamandre", False),
    ("Christian Fischbacher", "Scalamandre", False),
    ("Grey Watkins", "Scalamandre", False),
    ("Hinson", "Scalamandre", False),
    ("Jean Paul Gaultier", "Scalamandre", False),
    ("Lelievre", "Scalamandre", False),
    ("Nicolette Mayer", "Scalamandre", False),
    ("Old World Weavers", "Scalamandre", False),
    ("Sandberg", "Scalamandre", False),
    ("Schumacher", "Schumacher", False),
    ("Boråstapeter", "Schumacher", False),
    ("Seabrook", "Seabrook", False),
    ("Stout", "Stout", False),
    ("Surya", "Surya", False),
    ("Tempaper", "Tempaper", True),
    ("Walls Republic", "Walls Republic", True),
    ("York", "York", False),
    ("Antonina Vella", "York", False),
    ("Ashford House", "York", False),
    ("Aviva Stanoff", "York", False),
    ("Candice Olson", "York", False),
    ("Carey Lind Designs", "York", False),
    ("Erin & Ben Co.", "York", False),
    ("Florence Broadhurst", "York", False),
    ("Magnolia Home", "York", False),
    ("Missoni", "York", False),
    ("Patina Vie", "York", False),
    ("Rifle Paper Co.", "York", False),
    ("Rifle", "York", False),
    ("Ronald Redding Designs", "York", False),
    ("RoomMates", "York", False),
    ("Waverly", "York", False),
    ("York Designer Series", "York", False),
    ("York Wallcoverings", "York", False),
    ("Zoffany", "Zoffany", False),
    ("Morris & Co", "Zoffany", False),
    ("Harlequin", "Zoffany", False),
    ("Sanderson", "Zoffany", False),
    ("Scion", "Zoffany", False),
]


tags = [
    ('Traditional', 'Style'),
    ('Transitional', 'Style'),
    ('Contemporary', 'Style'),
    ('Coastal', 'Style'),
    ('Rustic', 'Style'),
    ('Global', 'Style'),

    ('Abstract', 'Category'),
    ('Animals', 'Category'),
    ('Birds', 'Category'),
    ('Asian', 'Category'),
    ('Beach', 'Category'),
    ('Check', 'Category'),
    ('Modern', 'Category'),
    ('Conversational', 'Category'),
    ('Damask', 'Category'),
    ('Diamond', 'Category'),
    ('Dots', 'Category'),
    ('Embroidery', 'Category'),
    ('Boho', 'Category'),
    ('Floral', 'Category'),
    ('Geometric', 'Category'),
    ('Herringbone', 'Category'),
    ('Ikat', 'Category'),
    ('Insects', 'Category'),
    ('Kids', 'Category'),
    ('Metallic', 'Category'),
    ('Outdoor', 'Category'),
    ('Paisley', 'Category'),
    ('Plaid', 'Category'),
    ('Quilted', 'Category'),
    ('Scroll', 'Category'),
    ('Sheer', 'Category'),
    ('Small Prints', 'Category'),
    ('Solid', 'Category'),
    ('Stripe', 'Category'),
    ('Texture', 'Category'),
    ('Toiles', 'Category'),
    ('Trellis', 'Category'),
    ('Applique', 'Category'),
    ('Braids', 'Category'),
    ('Cords', 'Category'),
    ('Cords with Tape', 'Category'),
    ('Fringe', 'Category'),
    ('Gimp', 'Category'),
    ('Rosettes', 'Category'),
    ('Tassel Fringe', 'Category'),
    ('Tassels', 'Category'),
    ('Tiebacks', 'Category'),
    ('Architectural Details', 'Category'),
    ('Borders', 'Category'),
    ('Faux Finishes', 'Category'),
    ('Grasscloth', 'Category'),
    ('Vinyl', 'Category'),
    ('Chevron', 'Category'),
    ('Leaves', 'Category'),
    ('Branches', 'Category'),
    ('Faux Bois', 'Category'),
    ('Shag', 'Category'),
    ('Cork', 'Category'),
    ('Hinson', 'Category'),
    ('Performance', 'Category'),
    ('Animal: Menagerie', 'Category'),
    ('Animal: Jungle', 'Category'),
    ('Animal: Safari', 'Category'),
    ('Animal: Leopard', 'Category'),
    ('Animal: Zebra', 'Category'),
    ('Animal: Lion', 'Category'),
    ('Animal: Tiger', 'Category'),
    ('Animal: Cheetah', 'Category'),
    ('Animal: Monkey', 'Category'),
    ('Animal: Dog', 'Category'),
    ('Animal: Cat', 'Category'),
    ('Animal: Snake', 'Category'),
    ('Animal: Lizard', 'Category'),
    ('Animal: Crocodile', 'Category'),
    ('Animal: Alligator', 'Category'),
    ('Animal: Dragon', 'Category'),
    ('Animal: Elephant', 'Category'),

    ('Black', 'Color'),
    ('Black/White', 'Color'),
    ('Blue', 'Color'),
    ('Blue/Green', 'Color'),
    ('Brown', 'Color'),
    ('Green', 'Color'),
    ('Grey', 'Color'),
    ('Multi', 'Color'),
    ('Beige', 'Color'),
    ('Orange', 'Color'),
    ('Pink', 'Color'),
    ('Purple', 'Color'),
    ('Red', 'Color'),
    ('Tan', 'Color'),
    ('White', 'Color'),
    ('Yellow', 'Color'),

    ('Leather', 'Content'),
    ('Wood', 'Content'),
    ('Chenille', 'Content'),
    ('Cotton', 'Content'),
    ('Jute, hemp, sea grass', 'Content'),
    ('Polyester', 'Content'),
    ('Silk', 'Content'),
    ('Wool', 'Content'),
    ('Cotton/Linen', 'Content'),
    ('Linen', 'Content'),
    ('Moire', 'Content'),
    ('Velvet', 'Content'),
    ('Glass', 'Content'),
    ('Metal', 'Content'),

    ('12" Diameter Sphere', 'Size'),
    ('18" Square', 'Size'),
    ('14" Square', 'Size'),
    ('16" Square', 'Size'),
    ('19" Square', 'Size'),
    ('20" Square', 'Size'),
    ('22" Square', 'Size'),
    ('24" Square', 'Size'),
    ('Lumbar', 'Size'),
    ('Up to 1"', 'Size'),
    ('1" to 2"', 'Size'),
    ('2" to 3"', 'Size'),
    ('3" to 4"', 'Size'),
    ('4" to 5"', 'Size'),
    ('5" and More', 'Size'),
    ("2' x 3'", 'Size'),
    ("3' x 5'", 'Size'),
    ("4' x 6'", 'Size'),
    ("5' x 7'", 'Size'),
    ("6' x 9'", 'Size'),
    ("8' x 10'", 'Size'),
    ("9' x 12'", 'Size'),
    ("10' x 14'", 'Size'),

    ('Square', 'Shape'),
    ('Round', 'Shape'),
    ('Rectangle', 'Shape'),

    ('$0 - $25', 'Price'),
    ('$25 - $50', 'Price'),
    ('$50 - $100', 'Price'),
    ('$100 - $200', 'Price'),
    ('$200 - $300', 'Price'),
    ('$300 - $400', 'Price'),
    ('$400 - $500', 'Price'),
    ('$500 & Up', 'Price'),

    ('Quick Ship', 'Group'),
    ('Outlet', 'Group'),
    ('Removable', 'Group'),
    ('Best Selling', 'Group'),
    ('No Sample', 'Group'),
    ('Cut Fee', 'Group'),
    ('White Glove', 'Group'),
    ('European', 'Group'),

    ('Aerin', 'Designer'),
    ('Alessandra Branca', 'Designer'),
    ('Alfred Shaheen', 'Designer'),
    ('Amy Lau', 'Designer'),
    ('Ankasa Iconic', 'Designer'),
    ('Barbara Barry', 'Designer'),
    ('Barclay Butera', 'Designer'),
    ('Calvin Klein', 'Designer'),
    ('Candice Olson', 'Designer'),
    ('Celerie Kemble', 'Designer'),
    ('Charlotte Moss', 'Designer'),
    ('Christie van der Haak', 'Designer'),
    ('Clodagh', 'Designer'),
    ('Dana Gibson', 'Designer'),
    ('Dwell Studio', 'Designer'),
    ('Echo Collection', 'Designer'),
    ('Eileen Kathryn Boyd', 'Designer'),
    ('Isaac Mizrahi', 'Designer'),
    ('Jonathan Adler', 'Designer'),
    ('Kathryn M Ireland', 'Designer'),
    ('Kelly Wearstler', 'Designer'),
    ('Larry Laslo', 'Designer'),
    ('Laura Kirar', 'Designer'),
    ('Lilly Pulitzer', 'Designer'),
    ('Marcus William', 'Designer'),
    ('Martyn Lawrence Bullard', 'Designer'),
    ('Mary McDonald', 'Designer'),
    ('Nate Berkus', 'Designer'),
    ('Oscar de la Renta', 'Designer'),
    ('Philip Gorrivan', 'Designer'),
    ('Pierre Deux', 'Designer'),
    ('Thom Filicia', 'Designer'),
    ('Thomas Paul', 'Designer'),
    ('Timothy Corrigan', 'Designer'),
    ('Trina Turk', 'Designer'),
    ('Windsor Smith', 'Designer'),
    ('Avalisa', 'Designer'),
    ('Coastal Living', 'Designer'),
    ('Counterfeit', 'Designer'),
    ('Grant Design', 'Designer'),
    ('Inhabit', 'Designer'),
    ('Jessica Swift', 'Designer'),
    ('Jet Designs', 'Designer'),
    ('Martha Stewart', 'Designer'),
    ('Smithsonian', 'Designer'),
    ('Hunt Slonem', 'Designer'),
    ('David Easton', 'Designer'),
    ('David Hicks', 'Designer'),
    ('Vern Yip', 'Designer'),
    ('Jaclyn Smith', 'Designer'),
    ('Joseph Abboud', 'Designer'),
    ('Kathy Ireland', 'Designer'),
    ('Michael Amini', 'Designer'),
    ('Jeffrey Alan Marks', 'Designer'),
    ('Michael Berman', 'Designer'),
    ('Suzanne Rheinstein', 'Designer'),
    ('Bunny Williams', 'Designer'),
    ('Kendall Wilkinson', 'Designer'),
    ('Florence Broadhurst', 'Designer'),
    ('Alexa Hampton', 'Designer'),
    ('James Huniford', 'Designer'),
    ('DwellStudio', 'Designer'),
    ('Miles Redd', 'Designer'),
    ('Missoni Home', 'Designer'),
    ('Madcap Cottage', 'Designer'),
    ('Stacy Garcia', 'Designer'),
    ('Aviva Stanoff', 'Designer'),
    ('Kate Spade', 'Designer'),
    ('Linherr Hollingsworth', 'Designer'),
    ('Ronald Redding', 'Designer'),
    ('Sarah Richardson', 'Designer'),
    ('Jan Showers', 'Designer'),
    ('Fornasetti', 'Designer'),
    ('Antonina Vella', 'Designer'),
    ('Johnson Hartig', 'Designer'),
    ('Barry Dixon', 'Designer'),
    ('Veere Greeney', 'Designer'),
    ('Caroline Z Hurley', 'Designer'),
    ('Vogue Living', 'Designer'),
    ('Mark D. Sikes', 'Designer'),
    ('Porter Teleo', 'Designer'),
    ('Molly Mahon', 'Designer'),
    ('Neisha Crosland', 'Designer'),
    ('Studio Bon', 'Designer'),
    ('David Oliver', 'Designer'),
    ('Matthew Patrick Smythe', 'Designer'),
    ('Colette Cosentino', 'Designer'),
]


class Command(BaseCommand):
    help = f"Migrate Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()

        if "type" in options['functions']:
            processor.type()

        if "manufacturer" in options['functions']:
            processor.manufacturer()

        if "tag" in options['functions']:
            processor.tag()

        if "shopify" in options['functions']:
            processor.shopify()

        if "cleanup" in options['functions']:
            processor.cleanup()


class Processor:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def type(self):
        Type.objects.all().delete()
        for name, parent in types:
            Type.objects.create(name=name, parent=parent)

    def manufacturer(self):
        Manufacturer.objects.all().delete()
        for name, brand, private in manufacturers:
            Manufacturer.objects.create(
                name=name, brand=brand, private=private)

    def tag(self):
        Tag.objects.all().delete()
        for name, type in tags:
            Tag.objects.create(name=name, type=type)

    def shopify(self):

        brands = [
            # ("Brewster", Brewster, False),
            ("Couture", Couture, False),
            ("Covington", Covington, True),
            # ("Dana Gibson", DanaGibson, False),
            # ("Elaine Smith", ElaineSmith, False),
            # ("Exquisite Rugs", ExquisiteRugs, False),
            ("Galerie", Galerie, False),
            # ("Hubbardton Forge", HubbardtonForge, False),
            # ("Jaipur Living", JaipurLiving, False),
            # ("Jamie Young", JamieYoung, False),
            # ("JF Fabrics", JFFabrics, False),
            # ("Kasmir", Kasmir, False),
            # ("Kravet", Kravet, False),
            # ("Materialworks", Materialworks, True),
            # ("Maxwell", Maxwell, False),
            # ("MindTheGap", MindTheGap, False),
            ("NOIR", NOIR, False),
            ("Olivia & Quinn", OliviaQuinn, False),
            ("P/Kaufmann", PKaufmann, False),
            ("Peninsula Home", PeninsulaHome, False),
            ("Phillip Jeffries", PhillipJeffries, False),
            ("Phillips Collection", PhillipsCollection, False),
            ("Pindler", Pindler, False),
            ("Poppy", Poppy, False),
            ("Port 68", Port68, False),
            ("Premier Prints", PremierPrints, True),
            # ("Scalamandre", Scalamandre, False),
            # ("Schumacher", Schumacher, False),
            ("Seabrook", Seabrook, False),
            ("Stout", Stout, False),
            # ("Surya", Surya, False),
            # ("Tempaper", Tempaper, True),
            ("York", York, False),
            # ("Zoffany", Zoffany, False),s
        ]

        for brandName, brand, private in brands:
            Product.objects.filter(manufacturer__brand=brandName).delete()

            products = brand.objects.all()

            total = len(products)

            def copyProduct(product, index):
                if not product.statusP:
                    return

                response = requests.request(
                    "GET",
                    f"https://www.decoratorsbestam.com/api/products/?sku={quote(product.sku)}",
                    headers={
                        'Authorization': 'Token d71bcdc1b60d358e01182da499fd16664a27877a'
                    }
                )
                try:
                    data = json.loads(response.text)["results"][0]
                except Exception as e:
                    debug.warn("Migrator", str(e))

                productId = data.get("productId", "")
                handle = data.get("handle", "")
                published = data.get("published", False)

                if productId and handle:
                    print(
                        f"{index}/{total} -- {product.sku}, {productId}, {handle}")

                    ###########
                    # Variant #
                    ###########
                    response = requests.request(
                        "GET",
                        f"https://www.decoratorsbestam.com/api/variants/?productid={productId}",
                        headers={
                            'Authorization': 'Token d71bcdc1b60d358e01182da499fd16664a27877a'
                        }
                    )
                    results = json.loads(response.text)["results"]

                    consumerId = ""
                    tradeId = ""
                    sampleId = ""
                    freeSampleId = ""

                    consumerPrice, tradePrice, samplePrice = common.markup(
                        brand=brandName, product=product, format=True)

                    for result in results:
                        if "Free Sample -" in result['name']:
                            freeSampleId = result['variantId']
                        elif "Sample -" in result['name']:
                            sampleId = result['variantId']
                        elif "Trade -" in result['name']:
                            tradeId = result['variantId']
                        else:
                            consumerId = result['variantId']

                    if not (consumerId and tradeId and sampleId and freeSampleId):
                        print(f"Variant Error. SKU: {newProduct.sku}")
                        return
                    ###########
                    # Variant #
                    ###########

                    if private:
                        manufacturerName = "DecoratorsBest"
                    else:
                        manufacturerName = product.manufacturer

                    if product.name:
                        title = f"{manufacturerName} {product.name}"
                    else:
                        title = f"{manufacturerName} {product.pattern} {product.color} {product.type}"

                    manufacturer = Manufacturer.objects.get(
                        name=product.manufacturer)

                    type = Type.objects.get(name=product.type)

                    if manufacturer and type:
                        try:
                            newProduct = Product.objects.create(
                                mpn=product.mpn,
                                sku=product.sku,

                                shopifyId=productId,
                                shopifyHandle=handle,

                                title=title,

                                pattern=product.pattern,
                                color=product.color,

                                manufacturer=manufacturer,
                                type=type,
                                collection=product.collection,

                                description=product.description,
                                width=product.width,
                                length=product.length,
                                height=product.height,
                                size=product.size,
                                repeatH=product.repeatH,
                                repeatV=product.repeatV,
                                specs=product.specs,

                                uom=product.uom,
                                minimum=product.minimum,
                                increment=product.increment,

                                yardsPR=product.yardsPR,
                                content=product.content,
                                match=product.match,
                                material=product.material,
                                finish=product.finish,
                                care=product.care,
                                country=product.country,
                                features=product.features,
                                usage=product.usage,
                                disclaimer=product.disclaimer,

                                consumerId=consumerId,
                                tradeId=tradeId,
                                sampleId=sampleId,
                                freeSampleId=freeSampleId,
                                cost=product.cost,
                                consumer=consumerPrice,
                                trade=tradePrice,
                                sample=samplePrice,
                                compare=None,
                                weight=product.weight,
                                barcode=product.upc,

                                published=published
                            )
                        except Exception as e:
                            debug.warn("Migrator", str(e))

            with ThreadPoolExecutor(max_workers=100) as executor:
                for index, product in enumerate(products):
                    executor.submit(copyProduct, product, index)

    def cleanup(self):

        shopifyManager = shopify.ShopifyManager()

        vendor_name = "Surya"

        base_url = f"https://decoratorsbest.myshopify.com/admin/api/2024-01/products.json"
        params = {'vendor': vendor_name, 'limit': 250, 'fields': 'id'}
        headers = {"X-Shopify-Access-Token": env('SHOPIFY_API_TOKEN')}

        session = requests.Session()
        session.headers.update(headers)

        response = session.get(base_url, params=params)

        page = 1
        while True:
            print(f"Reviewing Products {250 * (page - 1) + 1} - {250 * page}")

            product_ids = {str(product['id'])
                           for product in response.json()['products']}

            existing_product_ids = set(Product.objects.filter(
                manufacturer=vendor_name, shopifyId__in=product_ids).values_list('shopifyId', flat=True).distinct())

            products_to_delete = product_ids - existing_product_ids

            for product_id in products_to_delete:
                print(f"Delete: {product_id}")
                shopifyManager.deleteProduct(product_id)

            if 'next' in response.links:
                next_url = response.links['next']['url']
                response = session.get(next_url)
                page += 1
            else:
                break
