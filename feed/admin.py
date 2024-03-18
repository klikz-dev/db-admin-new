from django.contrib import admin

from .models import Brewster
from .models import Couture
from .models import Covington
from .models import DanaGibson
from .models import ElaineSmith
from .models import ExquisiteRugs
from .models import Galerie
from .models import HubbardtonForge
from .models import JaipurLiving
from .models import JamieYoung
from .models import JFFabrics
from .models import Kasmir
from .models import Kravet
from .models import Materialworks
from .models import Maxwell
from .models import MindTheGap
from .models import NOIR
from .models import OliviaQuinn
from .models import PeninsulaHome
from .models import PhillipsCollection
from .models import PhillipJeffries
from .models import Pindler
from .models import Port68
from .models import PremierPrints
from .models import Scalamandre
from .models import Schumacher
from .models import Seabrook
from .models import Stout
from .models import Surya
from .models import Tempaper
from .models import WallsRepublic
from .models import York
from .models import Zoffany


class FeedAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Primary Keys', {'fields': [
            'mpn',
            'sku',
            'pattern',
            'color',
            'name',
            'productId'
        ]}),
        ('Categorization', {'fields': [
            'brand',
            'manufacturer',
            'type',
            'collection'
        ]}),
        ('Main Information', {'fields': [
            'description',
            'width',
            'length',
            'height',
            'size',
            'repeatH',
            'repeatV',
            'specs',
        ]}),
        ('Additional Information', {'fields': [
            'yardsPR',
            'content',
            'match',
            'material',
            'finish',
            'care',
            'weight',
            'country',
            'features',
            'usage',
            'disclaimer',
            'upc',
        ]}),
        ('Pricing', {'fields': [
            'cost',
            'msrp',
            'map'
        ]}),
        ('Measurement', {'fields': [
            'uom',
            'minimum',
            'increment'
        ]}),
        ('Tagging', {'fields': [
            'keywords',
            'colors'
        ]}),
        ('Status', {'fields': [
            'statusP',
            'statusS',
            'european',
            'quickShip',
            'whiteGlove',
            'bestSeller',
            'outlet'
        ]}),
        ('Stock', {'fields': [
            'stockP',
            'stockS',
            'stockNote'
        ]}),
        ('Assets', {'fields': [
            'thumbnail',
            'roomsets'
        ]}),
        ('Additional', {'fields': [
            'custom',
        ]}),
    ]

    list_display = (
        'mpn',
        'sku',
        'pattern',
        'color',
        'productId',
        'type',
        'manufacturer',
        'collection',
        'cost',
        'map',
        'statusP',
        'statusS',
    )

    list_filter = [
        'brand',
        'type',
        'manufacturer',
        'uom',
        'statusP',
        'statusS',
        'whiteGlove',
        'quickShip',
        'collection',
    ]

    search_fields = [
        'mpn',
        'sku',
        'productId',
        'pattern',
        'color',
        'collection'
    ]


@admin.register(Brewster)
class BrewsterAdmin(FeedAdmin):
    pass


@admin.register(Couture)
class CoutureAdmin(FeedAdmin):
    pass


@admin.register(Covington)
class CovingtonAdmin(FeedAdmin):
    pass


@admin.register(DanaGibson)
class DanaGibsonAdmin(FeedAdmin):
    pass


@admin.register(ElaineSmith)
class ElaineSmithAdmin(FeedAdmin):
    pass


@admin.register(ExquisiteRugs)
class ExquisiteRugsAdmin(FeedAdmin):
    pass


@admin.register(Galerie)
class GalerieAdmin(FeedAdmin):
    pass


@admin.register(HubbardtonForge)
class HubbardtonForgeAdmin(FeedAdmin):
    pass


@admin.register(JaipurLiving)
class JaipurLivingAdmin(FeedAdmin):
    pass


@admin.register(JamieYoung)
class JamieYoungAdmin(FeedAdmin):
    pass


@admin.register(JFFabrics)
class JFFabricsAdmin(FeedAdmin):
    pass


@admin.register(Kasmir)
class KasmirAdmin(FeedAdmin):
    pass


@admin.register(Kravet)
class KravetAdmin(FeedAdmin):
    pass


@admin.register(Materialworks)
class MaterialworksAdmin(FeedAdmin):
    pass


@admin.register(Maxwell)
class MaxwellAdmin(FeedAdmin):
    pass


@admin.register(MindTheGap)
class MindTheGapAdmin(FeedAdmin):
    pass


@admin.register(NOIR)
class NOIRAdmin(FeedAdmin):
    pass


@admin.register(OliviaQuinn)
class OliviaQuinnAdmin(FeedAdmin):
    pass


@admin.register(PeninsulaHome)
class PeninsulaHomeAdmin(FeedAdmin):
    pass


@admin.register(PhillipJeffries)
class PhillipJeffriesAdmin(FeedAdmin):
    pass


@admin.register(PhillipsCollection)
class PhillipsCollectionAdmin(FeedAdmin):
    pass


@admin.register(Pindler)
class PindlerAdmin(FeedAdmin):
    pass


@admin.register(Port68)
class Port68Admin(FeedAdmin):
    pass


@admin.register(PremierPrints)
class PremierPrintsAdmin(FeedAdmin):
    pass


@admin.register(Scalamandre)
class ScalamandreAdmin(FeedAdmin):
    pass


@admin.register(Schumacher)
class SchumacherAdmin(FeedAdmin):
    pass


@admin.register(Seabrook)
class SeabrookAdmin(FeedAdmin):
    pass


@admin.register(Stout)
class StoutAdmin(FeedAdmin):
    pass


@admin.register(Surya)
class SuryaAdmin(FeedAdmin):
    pass


@admin.register(Tempaper)
class TempaperAdmin(FeedAdmin):
    pass


@admin.register(WallsRepublic)
class WallsRepublicAdmin(FeedAdmin):
    pass


@admin.register(York)
class YorkAdmin(FeedAdmin):
    pass


@admin.register(Zoffany)
class ZoffanyAdmin(FeedAdmin):
    pass
