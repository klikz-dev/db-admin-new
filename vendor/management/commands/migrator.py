from concurrent.futures import ThreadPoolExecutor
import requests
import json
import environ
import os
from urllib.parse import quote
from tqdm import tqdm
from django.db import transaction

from django.core.management.base import BaseCommand

from utils import common, debug, shopify, const
from vendor.models import Type, Manufacturer, Tag, Product, Image, Sync

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
from feed.models import KravetDecor
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

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

types = [
    ("Wallpaper", "Root"),
    ("Wall Art", "Root"),
    ("Trim", "Root"),
    ("Rug", "Root"),
    ("Pillow", "Root"),
    ("Mirror", "Root"),
    ("Lighting", "Root"),
    ("Furniture", "Root"),
    ("Fabric", "Root"),
    ("Accent", "Root"),
    ("Wastebasket", "Accent"),
    ("Vase", "Accent"),
    ("Tray", "Accent"),
    ("Tote", "Accent"),
    ("Tissue Box", "Accent"),
    ("Throw", "Accent"),
    ("Tabletop", "Accent"),
    ("Sculpture", "Accent"),
    ("Screen", "Accent"),
    ("Print", "Accent"),
    ("Pouf", "Accent"),
    ("Plate", "Accent"),
    ("Planter", "Accent"),
    ("Object", "Accent"),
    ("Ice Bucket", "Accent"),
    ("Hurricane", "Accent"),
    ("Ginger Jar", "Accent"),
    ("Decorative Bowl", "Accent"),
    ("Decorative Accent", "Accent"),
    ("Candlestick", "Accent"),
    ("Candleholder", "Accent"),
    ("Candle Holder", "Accent"),
    ("Cachepot", "Accent"),
    ("Box", "Accent"),
    ("Bowl", "Accent"),
    ("Bookend", "Accent"),
    ("Basket", "Accent"),
    ("Accessory", "Accent"),
    ("Upholstery Fabric", "Fabric"),
    ("Drapery Fabric", "Fabric"),
    ("Stool", "Furniture"),
    ("Sofa", "Furniture"),
    ("Side Table", "Furniture"),
    ("Ottoman", "Furniture"),
    ("Hutch", "Furniture"),
    ("Garden Stool", "Furniture"),
    ("End Table", "Furniture"),
    ("Dresser", "Furniture"),
    ("Dining Table", "Furniture"),
    ("Dining Chair", "Furniture"),
    ("Desk", "Furniture"),
    ("Counter Stool", "Furniture"),
    ("Console", "Furniture"),
    ("Coffee Table", "Furniture"),
    ("Cocktail Table", "Furniture"),
    ("Chair", "Furniture"),
    ("Cabinet", "Furniture"),
    ("Bookcase", "Furniture"),
    ("Bench", "Furniture"),
    ("Bed", "Furniture"),
    ("Bar Stool", "Furniture"),
    ("Accent Table", "Furniture"),
    ("Accent Chair", "Furniture"),
    ("Wall Sconce", "Lighting"),
    ("Torchier", "Lighting"),
    ("Table Lamp", "Lighting"),
    ("Semi-Flush Mount", "Lighting"),
    ("Pendant", "Lighting"),
    ("Lamp Shade", "Lighting"),
    ("Flush Mount", "Lighting"),
    ("Floor Lamp", "Lighting"),
    ("Chandelier", "Lighting"),
    ("Accent Lamp", "Lighting"),
    ("Square Mirror", "Mirror"),
    ("Round Mirror", "Mirror"),
    ("Rectangle Mirror", "Mirror"),
    ("Square Throw Pillow", "Pillow"),
    ("Rectangle Throw Pillow", "Pillow"),
    ("Pillow Kit", "Pillow"),
    ("Pillow Insert", "Pillow"),
    ("Pillow Cover", "Pillow"),
    ("Outdoor Pillow", "Pillow"),
    ("Decorative Pillow", "Pillow"),
    ("Rug Pad", "Rug"),
    ("Tieback", "Trim"),
    ("Tassel with Fringe", "Trim"),
    ("Tassel", "Trim"),
    ("Rosette", "Trim"),
    ("Gimp", "Trim"),
    ("Fringe", "Trim"),
    ("Cord with Tape", "Trim"),
    ("Cord", "Trim"),
    ("Braid", "Trim"),
    ("Applique", "Trim"),
    ("Wall Mirror", "Wall Art"),
    ("Wall Hanging", "Wall Art"),
    ("Wall Accent", "Wall Art"),
    ("Painting", "Wall Art"),
    ("Original Art", "Wall Art"),
    ("Mural", "Wallpaper"),
    ("Border", "Wallpaper"),
]

manufacturers = [
    ("Brewster Home Fashions", "Brewster", False),
    ("A-Street Prints", "Brewster", False),
    ("Couture", "Couture", False),
    ("Covington", "Covington", True),
    ("Dana Gibson", "Dana Gibson", False),
    ("Elaine Smith", "Elaine Smith", False),
    ("Exquisite Rugs", "Exquisite Rugs", False),
    ("Galerie", "Galerie", False),
    ("Hubbardton Forge", "Hubbardton Forge", False),
    ("Jaipur Living", "Jaipur Living", False),
    ("Jamie Young", "Jamie Young", False),
    ("JF Fabrics", "JF Fabrics", False),
    ("ILIV", "JF Fabrics", False),
    ("Caselio", "JF Fabrics", False),
    ("Casadeco", "JF Fabrics", False),
    ("Kasmir", "Kasmir", False),
    ("Winfield Thybony", "Kravet", False),
    ("Threads", "Kravet", False),
    ("Mulberry", "Kravet", False),
    ("Lizzo", "Kravet", False),
    ("Lee Jofa", "Kravet", False),
    ("Kravet", "Kravet", False),
    ("Gaston Y Daniela", "Kravet", False),
    ("G P & J Baker", "Kravet", False),
    ("Donghia", "Kravet", False),
    ("Cole & Son", "Kravet", False),
    ("Clarke & Clarke", "Kravet", False),
    ("Brunschwig & Fils", "Kravet", False),
    ("Baker Lifestyle", "Kravet", False),
    ("Andrew Martin", "Kravet", False),
    ("Kravet Decor", "Kravet Decor", False),
    ("Materialworks", "Materialworks", True),
    ("Maxwell", "Maxwell", False),
    ("MindTheGap", "MindTheGap", False),
    ("NOIR", "NOIR", False),
    ("Olivia & Quinn", "Olivia & Quinn", False),
    ("Tommy Bahama", "P/Kaufmann", False),
    ("Surface Style", "P/Kaufmann", False),
    ("Harrison Howard", "P/Kaufmann", False),
    ("Elana Gabrielle", "P/Kaufmann", False),
    ("Peninsula Home", "Peninsula Home", False),
    ("Phillip Jeffries", "Phillip Jeffries", False),
    ("Phillips Collection", "Phillips Collection", False),
    ("Pindler", "Pindler", False),
    ("Poppy Print Studio", "Poppy", False),
    ("Williamsburg", "Port 68", False),
    ("Scalamandre Maison", "Port 68", False),
    ("Madcap Cottage Décor", "Port 68", False),
    ("Premier Prints", "Premier Prints", True),
    ("Scalamandre", "Scalamandre", False),
    ("Sandberg", "Scalamandre", False),
    ("Old World Weavers", "Scalamandre", False),
    ("Nicolette Mayer", "Scalamandre", False),
    ("Lelievre", "Scalamandre", False),
    ("Jean Paul Gaultier", "Scalamandre", False),
    ("Hinson", "Scalamandre", False),
    ("Grey Watkins", "Scalamandre", False),
    ("Christian Fischbacher", "Scalamandre", False),
    ("Boris Kroll", "Scalamandre", False),
    ("Alhambra", "Scalamandre", False),
    ("Aldeco", "Scalamandre", False),
    ("Schumacher", "Schumacher", False),
    ("Boråstapeter", "Schumacher", False),
    ("Seabrook", "Seabrook", False),
    ("Stout", "Stout", False),
    ("Surya", "Surya", False),
    ("Tempaper", "Tempaper", True),
    ("York Wallcoverings", "York", False),
    ("York Designer Series", "York", False),
    ("York", "York", False),
    ("Waverly", "York", False),
    ("RoomMates", "York", False),
    ("Ronald Redding Designs", "York", False),
    ("Rifle Paper Co.", "York", False),
    ("Patina Vie", "York", False),
    ("Missoni", "York", False),
    ("Magnolia Home", "York", False),
    ("Florence Broadhurst", "York", False),
    ("Erin & Ben Co.", "York", False),
    ("Carey Lind Designs", "York", False),
    ("Candice Olson", "York", False),
    ("Aviva Stanoff", "York", False),
    ("Ashford House", "York", False),
    ("Antonina Vella", "York", False),
    ("Zoffany", "Zoffany", False),
    ("Scion", "Zoffany", False),
    ("Sanderson", "Zoffany", False),
    ("Morris & Co", "Zoffany", False),
    ("Harlequin", "Zoffany", False),
]


tags = [
    ('Vinyl', 'Category'),
    ('Trellis', 'Category'),
    ('Toiles', 'Category'),
    ('Tiebacks', 'Category'),
    ('Texture', 'Category'),
    ('Tassels', 'Category'),
    ('Tassel Fringe', 'Category'),
    ('Stripe', 'Category'),
    ('Solid', 'Category'),
    ('Small Prints', 'Category'),
    ('Sheer', 'Category'),
    ('Shag', 'Category'),
    ('Scroll', 'Category'),
    ('Rosettes', 'Category'),
    ('Quilted', 'Category'),
    ('Plaid', 'Category'),
    ('Performance', 'Category'),
    ('Paisley', 'Category'),
    ('Outdoor', 'Category'),
    ('Modern', 'Category'),
    ('Metallic', 'Category'),
    ('Leaves', 'Category'),
    ('Kids', 'Category'),
    ('Insects', 'Category'),
    ('Ikat', 'Category'),
    ('Hinson', 'Category'),
    ('Herringbone', 'Category'),
    ('Grasscloth', 'Category'),
    ('Gimp', 'Category'),
    ('Geometric', 'Category'),
    ('Fringe', 'Category'),
    ('Floral', 'Category'),
    ('Faux Finishes', 'Category'),
    ('Faux Bois', 'Category'),
    ('Embroidery', 'Category'),
    ('Dots', 'Category'),
    ('Diamond', 'Category'),
    ('Damask', 'Category'),
    ('Cork', 'Category'),
    ('Cords with Tape', 'Category'),
    ('Cords', 'Category'),
    ('Conversational', 'Category'),
    ('Chevron', 'Category'),
    ('Check', 'Category'),
    ('Branches', 'Category'),
    ('Braids', 'Category'),
    ('Borders', 'Category'),
    ('Boho', 'Category'),
    ('Birds', 'Category'),
    ('Beach', 'Category'),
    ('Asian', 'Category'),
    ('Architectural Details', 'Category'),
    ('Applique', 'Category'),
    ('Animals', 'Category'),
    ('Animal: Zebra', 'Category'),
    ('Animal: Tiger', 'Category'),
    ('Animal: Snake', 'Category'),
    ('Animal: Safari', 'Category'),
    ('Animal: Monkey', 'Category'),
    ('Animal: Menagerie', 'Category'),
    ('Animal: Lizard', 'Category'),
    ('Animal: Lion', 'Category'),
    ('Animal: Leopard', 'Category'),
    ('Animal: Jungle', 'Category'),
    ('Animal: Elephant', 'Category'),
    ('Animal: Dragon', 'Category'),
    ('Animal: Dog', 'Category'),
    ('Animal: Crocodile', 'Category'),
    ('Animal: Cheetah', 'Category'),
    ('Animal: Cat', 'Category'),
    ('Animal: Alligator', 'Category'),
    ('Abstract', 'Category'),
    ('Yellow', 'Color'),
    ('White', 'Color'),
    ('Tan', 'Color'),
    ('Red', 'Color'),
    ('Purple', 'Color'),
    ('Pink', 'Color'),
    ('Orange', 'Color'),
    ('Multi', 'Color'),
    ('Grey', 'Color'),
    ('Green', 'Color'),
    ('Brown', 'Color'),
    ('Blue/Green', 'Color'),
    ('Blue', 'Color'),
    ('Black/White', 'Color'),
    ('Black', 'Color'),
    ('Beige', 'Color'),
    ('Wool', 'Content'),
    ('Wood', 'Content'),
    ('Velvet', 'Content'),
    ('Silk', 'Content'),
    ('Polyester', 'Content'),
    ('Moire', 'Content'),
    ('Metal', 'Content'),
    ('Linen', 'Content'),
    ('Leather', 'Content'),
    ('Jute, hemp, sea grass', 'Content'),
    ('Glass', 'Content'),
    ('Cotton/Linen', 'Content'),
    ('Cotton', 'Content'),
    ('Chenille', 'Content'),
    ('Windsor Smith', 'Designer'),
    ('Vogue Living', 'Designer'),
    ('Vern Yip', 'Designer'),
    ('Veere Greeney', 'Designer'),
    ('Trina Turk', 'Designer'),
    ('Timothy Corrigan', 'Designer'),
    ('Thomas Paul', 'Designer'),
    ('Thom Filicia', 'Designer'),
    ('Suzanne Rheinstein', 'Designer'),
    ('Studio Bon', 'Designer'),
    ('Stacy Garcia', 'Designer'),
    ('Smithsonian', 'Designer'),
    ('Sarah Richardson', 'Designer'),
    ('Ronald Redding', 'Designer'),
    ('Porter Teleo', 'Designer'),
    ('Pierre Deux', 'Designer'),
    ('Philip Gorrivan', 'Designer'),
    ('Oscar de la Renta', 'Designer'),
    ('Neisha Crosland', 'Designer'),
    ('Nate Berkus', 'Designer'),
    ('Molly Mahon', 'Designer'),
    ('Missoni Home', 'Designer'),
    ('Miles Redd', 'Designer'),
    ('Michael Berman', 'Designer'),
    ('Michael Amini', 'Designer'),
    ('Matthew Patrick Smythe', 'Designer'),
    ('Mary McDonald', 'Designer'),
    ('Martyn Lawrence Bullard', 'Designer'),
    ('Martha Stewart', 'Designer'),
    ('Mark D. Sikes', 'Designer'),
    ('Marcus William', 'Designer'),
    ('Madcap Cottage', 'Designer'),
    ('Linherr Hollingsworth', 'Designer'),
    ('Lilly Pulitzer', 'Designer'),
    ('Laura Kirar', 'Designer'),
    ('Larry Laslo', 'Designer'),
    ('Kendall Wilkinson', 'Designer'),
    ('Kelly Wearstler', 'Designer'),
    ('Kathy Ireland', 'Designer'),
    ('Kathryn M Ireland', 'Designer'),
    ('Kate Spade', 'Designer'),
    ('Joseph Abboud', 'Designer'),
    ('Jonathan Adler', 'Designer'),
    ('Johnson Hartig', 'Designer'),
    ('Jet Designs', 'Designer'),
    ('Jessica Swift', 'Designer'),
    ('Jeffrey Alan Marks', 'Designer'),
    ('Jan Showers', 'Designer'),
    ('James Huniford', 'Designer'),
    ('Jaclyn Smith', 'Designer'),
    ('Isaac Mizrahi', 'Designer'),
    ('Inhabit', 'Designer'),
    ('Hunt Slonem', 'Designer'),
    ('Grant Design', 'Designer'),
    ('Fornasetti', 'Designer'),
    ('Florence Broadhurst', 'Designer'),
    ('Eileen Kathryn Boyd', 'Designer'),
    ('Echo Collection', 'Designer'),
    ('DwellStudio', 'Designer'),
    ('Dwell Studio', 'Designer'),
    ('David Oliver', 'Designer'),
    ('David Hicks', 'Designer'),
    ('David Easton', 'Designer'),
    ('Dana Gibson', 'Designer'),
    ('Counterfeit', 'Designer'),
    ('Colette Cosentino', 'Designer'),
    ('Coastal Living', 'Designer'),
    ('Clodagh', 'Designer'),
    ('Christie van der Haak', 'Designer'),
    ('Charlotte Moss', 'Designer'),
    ('Celerie Kemble', 'Designer'),
    ('Caroline Z Hurley', 'Designer'),
    ('Candice Olson', 'Designer'),
    ('Calvin Klein', 'Designer'),
    ('Bunny Williams', 'Designer'),
    ('Barry Dixon', 'Designer'),
    ('Barclay Butera', 'Designer'),
    ('Barbara Barry', 'Designer'),
    ('Aviva Stanoff', 'Designer'),
    ('Avalisa', 'Designer'),
    ('Antonina Vella', 'Designer'),
    ('Ankasa Iconic', 'Designer'),
    ('Amy Lau', 'Designer'),
    ('Alfred Shaheen', 'Designer'),
    ('Alexa Hampton', 'Designer'),
    ('Alessandra Branca', 'Designer'),
    ('Aerin', 'Designer'),
    ('White Glove', 'Group'),
    ('Removable', 'Group'),
    ('Quick Ship', 'Group'),
    ('Outlet', 'Group'),
    ('No Sample', 'Group'),
    ('European', 'Group'),
    ('Cut Fee', 'Group'),
    ('Best Selling', 'Group'),
    ('$500 & Up', 'Price'),
    ('$50 - $100', 'Price'),
    ('$400 - $500', 'Price'),
    ('$300 - $400', 'Price'),
    ('$25 - $50', 'Price'),
    ('$200 - $300', 'Price'),
    ('$100 - $200', 'Price'),
    ('$0 - $25', 'Price'),
    ('Square', 'Shape'),
    ('Round', 'Shape'),
    ('Rectangle', 'Shape'),
    ('Up to 1"', 'Size'),
    ('Lumbar', 'Size'),
    ("9' x 12'", 'Size'),
    ("8' x 10'", 'Size'),
    ("6' x 9'", 'Size'),
    ('5" and More', 'Size'),
    ("5' x 7'", 'Size'),
    ('4" to 5"', 'Size'),
    ("4' x 6'", 'Size'),
    ('3" to 4"', 'Size'),
    ("3' x 5'", 'Size'),
    ('24" Square', 'Size'),
    ('22" Square', 'Size'),
    ('20" Square', 'Size'),
    ('2" to 3"', 'Size'),
    ("2' x 3'", 'Size'),
    ('19" Square', 'Size'),
    ('18" Square', 'Size'),
    ('16" Square', 'Size'),
    ('14" Square', 'Size'),
    ('12" Diameter Sphere', 'Size'),
    ("10' x 14'", 'Size'),
    ('1" to 2"', 'Size'),
    ('Transitional', 'Style'),
    ('Traditional', 'Style'),
    ('Rustic', 'Style'),
    ('Global', 'Style'),
    ('Contemporary', 'Style'),
    ('Coastal', 'Style'),
]


class Command(BaseCommand):
    help = f"Migrate Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()

        # if "type" in options['functions']:
        #     processor.type()

        # if "manufacturer" in options['functions']:
        #     processor.manufacturer()

        # if "tag" in options['functions']:
        #     processor.tag()

        # if "shopify" in options['functions']:
        #     processor.shopify()

        # if "image" in options['functions']:
        #     processor.image()

        if "cleanup" in options['functions']:
            processor.cleanup()

        if "collections" in options['functions']:
            processor.collections()

        if "sync-status" in options['functions']:
            processor.syncStatus()

        if "sync-price" in options['functions']:
            processor.syncPrice()

        if "sync-tag" in options['functions']:
            processor.syncTag()

        if "sync-content" in options['functions']:
            processor.syncContent()


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
            # ("Couture", Couture, False),
            # ("Covington", Covington, True),
            # ("Dana Gibson", DanaGibson, False),
            # ("Elaine Smith", ElaineSmith, False),
            # ("Exquisite Rugs", ExquisiteRugs, False),
            # ("Galerie", Galerie, False),
            # ("Hubbardton Forge", HubbardtonForge, False),
            # ("Jaipur Living", JaipurLiving, False),
            # ("Jamie Young", JamieYoung, False),
            # ("JF Fabrics", JFFabrics, False),
            # ("Kasmir", Kasmir, False),
            # ("Kravet", Kravet, False),
            # ("Kravet Decor", KravetDecor, False),
            # ("Materialworks", Materialworks, True),
            # ("Maxwell", Maxwell, False),
            # ("MindTheGap", MindTheGap, False),
            # ("NOIR", NOIR, False),
            # ("Olivia & Quinn", OliviaQuinn, False),
            # ("P/Kaufmann", PKaufmann, False),
            # ("Peninsula Home", PeninsulaHome, False),
            # ("Phillip Jeffries", PhillipJeffries, False),
            # ("Phillips Collection", PhillipsCollection, False),
            # ("Pindler", Pindler, False),
            # ("Poppy", Poppy, False),
            # ("Port 68", Port68, False),
            # ("Premier Prints", PremierPrints, True),
            # ("Scalamandre", Scalamandre, False),
            # ("Schumacher", Schumacher, False),
            # ("Seabrook", Seabrook, False),
            # ("Stout", Stout, False),
            # ("Surya", Surya, False),
            # ("Tempaper", Tempaper, True),
            # ("York", York, False),
            # ("Zoffany", Zoffany, False),
        ]

        for brandName, brand, private in brands:
            Product.objects.filter(manufacturer__brand=brandName).delete()

            products = brand.objects.all()

            total = len(products)

            # for index, product in enumerate(products):
            def copyProduct(index, product):

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

                    markup = const.markup[product.brand]
                    if product.type in markup:
                        markup = markup[product.type]
                    if product.european and "European" in markup:
                        markup = markup["European"]

                    cost = product.cost
                    consumer = common.toPrice(cost, markup['consumer'])
                    trade = common.toPrice(cost, markup['trade'])
                    sample = 15 if product.type == "Rug" else 5

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
                                cost=cost,
                                consumer=consumer,
                                trade=trade,
                                sample=sample,
                                compare=None,
                                weight=product.weight,
                                barcode=product.upc,

                                published=published
                            )
                        except Exception as e:
                            debug.warn("Migrator", str(e))

            with ThreadPoolExecutor(max_workers=100) as executor:
                for index, product in enumerate(products):
                    executor.submit(copyProduct, index, product)

    def requestAPI(self, url):
        responseData = requests.get(
            url,
            headers={
                'Authorization': 'Token d71bcdc1b60d358e01182da499fd16664a27877a'
            }
        )
        responseJson = json.loads(responseData.text)

        return responseJson

    def image(self):
        Image.objects.filter(product__manufacturer__brand="York").delete()

        products = Product.objects.filter(manufacturer__brand="York")
        total = len(products)

        def importImage(index, product):
            imagesData = self.requestAPI(
                f"https://www.decoratorsbestam.com/api/images/?product={product.shopifyId}")

            imagesArray = imagesData['results']

            for image in imagesArray:
                imageURL = image['imageURL']
                imageIndex = image['imageIndex']

                if imageIndex == 20:
                    continue

                Image.objects.update_or_create(
                    url=imageURL,
                    position=imageIndex,
                    product=product,
                    hires=False,
                )

                debug.log(
                    "Migrator", f"{index}/{total} - {product} image {imageURL}")

        with ThreadPoolExecutor(max_workers=100) as executor:
            for index, product in enumerate(products):
                executor.submit(importImage, index, product)

    def cleanup(self):

        # Temp: Enable JFF Casadeco, Caselio, ILIV
        shopifyManager = shopify.ShopifyManager()

        vendors = ["Casadeco", "Caselio", "ILIV"]
        for vendor_name in vendors:
            base_url = f"https://decoratorsbest.myshopify.com/admin/api/2024-01/products.json"
            params = {'vendor': vendor_name,
                      'limit': 250, 'fields': 'id,title'}
            headers = {"X-Shopify-Access-Token": env('SHOPIFY_API_TOKEN')}

            session = requests.Session()
            session.headers.update(headers)

            response = session.get(base_url, params=params)

            page = 1
            while True:
                print(
                    f"Reviewing Products {250 * (page - 1) + 1} - {250 * page}")

                products = response.json()['products']

                product_ids = {
                    str(product['id']) for product in products}

                existing_product_ids = set(Product.objects.filter(
                    shopifyId__in=product_ids).values_list('shopifyId', flat=True).distinct())

                products_to_remove = product_ids - existing_product_ids

                for product_id in products_to_remove:
                    print(f"Publish: {product_id}")

                    shopifyManager.updateProductStatus(
                        productId=product_id, status=True)

                    shopifyManager.requestAPI(
                        method="PUT",
                        url=f"/products/{product_id}.json",
                        payload={
                            "product":
                            {
                                'id': product_id,
                                "tags": "Group:No Sample",
                            }
                        }
                    )

                if 'next' in response.links:
                    next_url = response.links['next']['url']
                    response = session.get(next_url)
                    page += 1
                else:
                    break

        return

        shopifyManager = shopify.ShopifyManager()

        base_url = f"https://decoratorsbest.myshopify.com/admin/api/2024-01/products.json"
        params = {'limit': 250, 'fields': 'id,published_at'}
        headers = {"X-Shopify-Access-Token": env('SHOPIFY_API_TOKEN')}

        session = requests.Session()
        session.headers.update(headers)

        response = session.get(base_url, params=params)

        page = 1
        while True:
            print(f"Reviewing Products {250 * (page - 1) + 1} - {250 * page}")

            products = response.json()['products']
            product_ids = {
                str(product['id']) for product in products if product['published_at'] is not None}

            existing_product_ids = set(Product.objects.filter(
                shopifyId__in=product_ids).values_list('shopifyId', flat=True).distinct())

            products_to_remove = product_ids - existing_product_ids

            for product_id in products_to_remove:
                print(f"Unpublish: {product_id}")

                shopifyManager.updateProductStatus(
                    productId=product_id, status=False)

                # shopifyManager.deleteProduct(product_id)

            if 'next' in response.links:
                next_url = response.links['next']['url']
                response = session.get(next_url)
                page += 1
            else:
                break

    def collections(self):

        base_url = f"https://decoratorsbest.myshopify.com/admin/api/2024-01/smart_collections.json"
        params = {'limit': 250, 'fields': 'id,handle,rules'}
        headers = {"X-Shopify-Access-Token": env('SHOPIFY_API_TOKEN')}

        session = requests.Session()
        session.headers.update(headers)

        response = session.get(base_url, params=params)

        oldRules = []

        page = 1
        while True:
            print(
                f"Reviewing Collections {250 * (page - 1) + 1} - {250 * page}")

            collections = response.json()['smart_collections']

            for collection in collections:
                print(f"Updating: {collection['handle']}")

                oldRules.append({
                    'id': collection['id'],
                    'handle': collection['handle'],
                    'rules': collection['rules']
                })

                # newRules = []
                # for rule in rules:
                #     oldRules.append(rules)

                #     if "mws_fee_generated" == rule['condition'] or "Product Fee" == rule['condition'] or "mw_hidden_cart_fee" == rule['condition']:
                #         continue
                #     newRule = {
                #         'column': rule['column'],
                #         'relation': rule['relation'],
                #         'condition': rule['condition'].replace("p_color:", "Color:"),
                #     }
                #     newRules.append(newRule)

                # try:
                #     requests.request(
                #         "PUT",
                #         f"https://decoratorsbest.myshopify.com/admin/api/2024-01/smart_collections/{collection['id']}.json",
                #         headers=headers,
                #         json={
                #             "smart_collection": {
                #                 "rules": newRules
                #             }
                #         }
                #     )
                # except Exception as e:
                #     print(e)
                #     continue

            if 'next' in response.links:
                next_url = response.links['next']['url']
                response = session.get(next_url)
                page += 1
            else:
                break

        newRules = oldRules

        for i, rulesData in enumerate(newRules):
            rules = rulesData['rules']
            for index, rule in enumerate(rules):
                if rule['column'] == "type" and "Throw Pillows" == rule['condition']:
                    rules[index]['condition'] = "Pillow"

            newRules[i]['rules'] = rules

        for collection in newRules:
            try:
                requests.request(
                    "PUT",
                    f"https://decoratorsbest.myshopify.com/admin/api/2024-01/smart_collections/{collection['id']}.json",
                    headers=headers,
                    json={
                        "smart_collection": {
                            "rules": collection['rules']
                        }
                    }
                )

                print(collection['handle'])
            except Exception as e:
                print(e)
                continue

        # with open(f"{FILEDIR}/collections.json", 'w') as outfile:
        #     json.dump(oldRules, outfile, indent=2)

        # with open(f"{FILEDIR}/new_collections.json", 'w') as outfile:
        #     json.dump(newRules, outfile, indent=2)

    def syncStatus(self):

        Sync.objects.filter(type="Status").delete()

        product_ids = Product.objects.values_list('shopifyId', flat=True)

        sync_objects = [Sync(productId=shopify_id, type="Status")
                        for shopify_id in product_ids]

        with transaction.atomic():
            try:
                Sync.objects.bulk_create(sync_objects)
            except Exception as e:
                print(e)

    def syncPrice(self):

        Sync.objects.filter(type="Price").delete()

        product_ids = Product.objects.values_list('shopifyId', flat=True)

        sync_objects = [Sync(productId=shopify_id, type="Price")
                        for shopify_id in product_ids]

        with transaction.atomic():
            try:
                Sync.objects.bulk_create(sync_objects)
            except Exception as e:
                print(e)

    def syncTag(self):

        Sync.objects.filter(type="Tag").delete()

        product_ids = Product.objects.values_list('shopifyId', flat=True)

        sync_objects = [Sync(productId=shopify_id, type="Tag")
                        for shopify_id in product_ids]

        with transaction.atomic():
            try:
                Sync.objects.bulk_create(sync_objects)
            except Exception as e:
                print(e)

    def syncContent(self):

        Sync.objects.filter(type="Content").delete()

        product_ids = Product.objects.values_list('shopifyId', flat=True)

        sync_objects = [Sync(productId=shopify_id, type="Content")
                        for shopify_id in product_ids]

        with transaction.atomic():
            try:
                Sync.objects.bulk_create(sync_objects)
            except Exception as e:
                print(e)
