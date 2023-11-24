from django.core.management.base import BaseCommand
from vendor.models import Type, Manufacturer

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


class Command(BaseCommand):
    help = f"Migrate Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "type" in options['functions']:
            processor = Processor()
            processor.type()

        if "manufacturer" in options['functions']:
            processor = Processor()
            processor.manufacturer()


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
