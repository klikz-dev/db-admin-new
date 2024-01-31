import requests
import json

from django.core.management.base import BaseCommand

from vendor.models import Type, Manufacturer, Tag, Product, Variant
from feed.models import Tempaper
from utils import common

types = [
    ("Fabric", "Root"),
    ("Wallpaper", "Root"),
    ("Trim", "Root"),
    ("Rug", "Root"),
    ("Pillow", "Root"),
    ("Furniture", "Root"),
    ("Lighting", "Root"),
    ("Accents", "Root"),
    ("Mirrors", "Root"),
    ("Wall Art", "Root"),
    ("Drapery Fabric", "Fabric"),
    ("Upholstery Fabric", "Fabric"),
    ("Murals", "Wallpaper"),
    ("Borders", "Wallpaper"),
    ("Applique", "Trim"),
    ("Braids", "Trim"),
    ("Cords", "Trim"),
    ("Cords With Tape", "Trim"),
    ("Fringe", "Trim"),
    ("Gimp", "Trim"),
    ("Rosettes", "Trim"),
    ("Tassels With Fringe", "Trim"),
    ("Tassels", "Trim"),
    ("Tiebacks", "Trim"),
    ("Rug Pad", "Rug"),
    ("Rectangle Throw Pillows", "Pillow"),
    ("Square Throw Pillows", "Pillow"),
    ("Pillow Cover", "Pillow"),
    ("Pillow Insert", "Pillow"),
    ("Pillow Kit", "Pillow"),
    ("Decorative Pillows", "Pillow"),
    ("Outdoor Pillows", "Pillow"),
    ("Beds", "Furniture"),
    ("Benches", "Furniture"),
    ("Bookcases", "Furniture"),
    ("Cabinets", "Furniture"),
    ("Chairs", "Furniture"),
    ("Consoles", "Furniture"),
    ("Coffee Tables", "Furniture"),
    ("Desks", "Furniture"),
    ("Sofas", "Furniture"),
    ("Side Tables", "Furniture"),
    ("Ottomans", "Furniture"),
    ("Stools", "Furniture"),
    ("Bar Stools", "Furniture"),
    ("Counter Stools", "Furniture"),
    ("Dining Chairs", "Furniture"),
    ("Accent Chairs", "Furniture"),
    ("Accent Tables", "Furniture"),
    ("Dressers", "Furniture"),
    ("End Tables", "Furniture"),
    ("Garden Stools", "Furniture"),
    ("Dining Tables", "Furniture"),
    ("Cocktail Tables", "Furniture"),
    ("Hutches", "Furniture"),
    ("Chandeliers", "Lighting"),
    ("Floor Lamps", "Lighting"),
    ("Table Lamps", "Lighting"),
    ("Wall Sconces", "Lighting"),
    ("Pendants", "Lighting"),
    ("Flush Mounts", "Lighting"),
    ("Semi-Flush Mounts", "Lighting"),
    ("Accent Lamps", "Lighting"),
    ("Lamp Shade", "Lighting"),
    ("Torchieres", "Lighting"),
    ("Rectangle Mirrors", "Mirrors"),
    ("Round Mirrors", "Mirrors"),
    ("Square Mirrors", "Mirrors"),
    ("Accessories", "Accents"),
    ("Table Top", "Accents"),
    ("Prints", "Accents"),
    ("Plate", "Accents"),
    ("Bookends", "Accents"),
    ("Bowls", "Accents"),
    ("Boxes", "Accents"),
    ("Candlesticks", "Accents"),
    ("Planters", "Accents"),
    ("Screens", "Accents"),
    ("Sculpture", "Accents"),
    ("Trays", "Accents"),
    ("Vases", "Accents"),
    ("Wastebaskets", "Accents"),
    ("Throws", "Accents"),
    ("Baskets", "Accents"),
    ("Candle Holders", "Accents"),
    ("Decorative Bowls", "Accents"),
    ("Hurricanes", "Accents"),
    ("Objects", "Accents"),
    ("Candleholders", "Accents"),
    ("Cachepot", "Accents"),
    ("Ginger Jar", "Accents"),
    ("Ice Bucket", "Accents"),
    ("Tote", "Accents"),
    ("Decorative Accents", "Accents"),
    ("Tissue Box", "Accents"),
    ("Pouf", "Accents"),
    ("Paintings", "Wall Art"),
    ("Wall Hangings", "Wall Art"),
    ("Original Art", "Wall Art"),
    ("Wall Accent", "Wall Art"),
    ("Wall Mirrors", "Wall Art"),
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
    ('Square', 'Shape'),
    ('Round', 'Shape'),
    ('Rectangle', 'Shape'),
    ("2' x 3'", 'Size'),
    ("3' x 5'", 'Size'),
    ("4' x 6'", 'Size'),
    ("5' x 7'", 'Size'),
    ("6' x 9'", 'Size'),
    ("8' x 10'", 'Size'),
    ("9' x 12'", 'Size'),
    ("10' x 14'", 'Size'),
    ('Quick Ship', 'Group'),
    ('Outlet', 'Group'),
    ('Removable', 'Group'),
    ('Best Selling', 'Group'),
    ('No Sample', 'Group'),
    ('Cut Fee', 'Group'),
    ('White Glove', 'Group'),
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
    ('Menagerie', 'SubCategory: Animal'),
    ('Jungle', 'SubCategory: Animal'),
    ('Safari', 'SubCategory: Animal'),
    ('Leopard', 'SubCategory: Animal'),
    ('Zebra', 'SubCategory: Animal'),
    ('Lion', 'SubCategory: Animal'),
    ('Tiger', 'SubCategory: Animal'),
    ('Cheetah', 'SubCategory: Animal'),
    ('Monkey', 'SubCategory: Animal'),
    ('Dog', 'SubCategory: Animal'),
    ('Cat', 'SubCategory: Animal'),
    ('Snake', 'SubCategory: Animal'),
    ('Lizard', 'SubCategory: Animal'),
    ('Crocodile', 'SubCategory: Animal'),
    ('Alligator', 'SubCategory: Animal'),
    ('Dragon', 'SubCategory: Animal'),
    ('Elephant', 'SubCategory: Animal'),
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
            ("Tempaper", Tempaper, True)  # Vendor Name, Vendor Model, Private
        ]

        for brandName, brand, private in brands:
            Product.objects.filter(manufacturer=brandName).delete()

            products = brand.objects.all()
            for product in products:
                response = requests.request(
                    "GET",
                    f"https://www.decoratorsbestam.com/api/products/?sku={product.sku}",
                    headers={
                        'Authorization': 'Token d71bcdc1b60d358e01182da499fd16664a27877a'
                    }
                )
                data = json.loads(response.text)["results"][0]
                productId = data.get("productId", "")
                handle = data.get("handle", "")
                published = data.get("published", False)

                if productId and handle and published:
                    print(product.sku, productId, handle)

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
                        continue
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
                            repeatH=product.repeatH,
                            repeatV=product.repeatV,
                            specs=product.specs,

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
