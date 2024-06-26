from django.db import models


class Feed(models.Model):
    mpn = models.CharField(max_length=200, primary_key=True)
    sku = models.CharField(max_length=200, unique=True,
                           null=False, blank=False)
    pattern = models.CharField(max_length=200, null=False, blank=False)
    color = models.CharField(max_length=200, null=False, blank=False)
    name = models.CharField(max_length=200, unique=True,
                            null=False, blank=False)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(max_length=200, null=False, blank=False)
    manufacturer = models.CharField(max_length=200, null=False, blank=False)
    type = models.CharField(max_length=200, null=False, blank=False)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=5000, default=None, null=True, blank=True)
    width = models.FloatField(default=0, null=True, blank=True)
    length = models.FloatField(default=0, null=True, blank=True)
    height = models.FloatField(default=0, null=True, blank=True)
    size = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    repeatH = models.FloatField(default=0, null=True, blank=True)
    repeatV = models.FloatField(default=0, null=True, blank=True)
    specs = models.JSONField(default=None, null=True, blank=True)

    yardsPR = models.FloatField(default=0, null=True, blank=True)
    content = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    match = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    material = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    finish = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    care = models.CharField(
        max_length=1000, default=None, null=True, blank=True)
    weight = models.FloatField(default=1, null=True, blank=True)
    country = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    features = models.JSONField(
        default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    disclaimer = models.CharField(
        max_length=2000, default=None, null=True, blank=True)
    upc = models.CharField(max_length=200, default=None, null=True, blank=True)

    cost = models.FloatField(null=False, blank=False)
    msrp = models.FloatField(default=0, null=True, blank=True)
    map = models.FloatField(default=0, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.IntegerField(default=1)

    keywords = models.CharField(
        max_length=2000, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=1000, default=None, null=True, blank=True)

    statusP = models.BooleanField(default=False)
    statusS = models.BooleanField(default=False)
    european = models.BooleanField(default=False)
    quickShip = models.BooleanField(default=False)
    whiteGlove = models.BooleanField(default=False)
    bestSeller = models.BooleanField(default=False)
    outlet = models.BooleanField(default=False)

    stockP = models.IntegerField(default=0)
    stockS = models.IntegerField(default=0)
    stockNote = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomsets = models.JSONField(default=None, null=True, blank=True)
    hires = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    custom = models.JSONField(default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn

    class Meta:
        abstract = True


class Brewster(Feed):
    class Meta:
        verbose_name = "Brewster"
        verbose_name_plural = "Brewster"


class Couture(Feed):
    class Meta:
        verbose_name = "Couture"
        verbose_name_plural = "Couture"


class Covington(Feed):
    class Meta:
        verbose_name = "Covington"
        verbose_name_plural = "Covington"


class DanaGibson(Feed):
    class Meta:
        verbose_name = "Dana Gibson"
        verbose_name_plural = "Dana Gibson"


class ElaineSmith(Feed):
    class Meta:
        verbose_name = "Elaine Smith"
        verbose_name_plural = "Elaine Smith"


class ExquisiteRugs(Feed):
    class Meta:
        verbose_name = "Exquisite Rugs"
        verbose_name_plural = "Exquisite Rugs"


class Galerie(Feed):
    class Meta:
        verbose_name = "Galerie"
        verbose_name_plural = "Galerie"


class HubbardtonForge(Feed):
    class Meta:
        verbose_name = "Hubbardton Forge"
        verbose_name_plural = "Hubbardton Forge"


class JaipurLiving(Feed):
    class Meta:
        verbose_name = "Jaipur Living"
        verbose_name_plural = "Jaipur Living"


class JamieYoung(Feed):
    class Meta:
        verbose_name = "Jamie Young"
        verbose_name_plural = "Jamie Young"


class JFFabrics(Feed):
    class Meta:
        verbose_name = "JF Fabrics"
        verbose_name_plural = "JF Fabrics"


class Kasmir(Feed):
    class Meta:
        verbose_name = "Kasmir"
        verbose_name_plural = "Kasmir"


class Kravet(Feed):
    class Meta:
        verbose_name = "Kravet"
        verbose_name_plural = "Kravet"


class KravetDecor(Feed):
    class Meta:
        verbose_name = "Kravet Decor"
        verbose_name_plural = "Kravet Decor"


class Materialworks(Feed):
    class Meta:
        verbose_name = "Materialworks"
        verbose_name_plural = "Materialworks"


class Maxwell(Feed):
    class Meta:
        verbose_name = "Maxwell"
        verbose_name_plural = "Maxwell"


class MindTheGap(Feed):
    class Meta:
        verbose_name = "MindTheGap"
        verbose_name_plural = "MindTheGap"


class NOIR(Feed):
    class Meta:
        verbose_name = "NOIR"
        verbose_name_plural = "NOIR"


class OliviaQuinn(Feed):
    class Meta:
        verbose_name = "Olivia & Quinn"
        verbose_name_plural = "Olivia & Quinn"


class PeninsulaHome(Feed):
    class Meta:
        verbose_name = "Peninsula Home"
        verbose_name_plural = "Peninsula Home"


class PhillipJeffries(Feed):
    class Meta:
        verbose_name = "Phillip Jeffries"
        verbose_name_plural = "Phillip Jeffries"


class PhillipsCollection(Feed):
    class Meta:
        verbose_name = "Phillips Collection"
        verbose_name_plural = "Phillips Collection"


class Pindler(Feed):
    class Meta:
        verbose_name = "Pindler"
        verbose_name_plural = "Pindler"


class PKaufmann(Feed):
    class Meta:
        verbose_name = "P/Kaufmann"
        verbose_name_plural = "P/Kaufmann"


class Poppy(Feed):
    class Meta:
        verbose_name = "Poppy"
        verbose_name_plural = "Poppy"


class Port68(Feed):
    class Meta:
        verbose_name = "Port 68"
        verbose_name_plural = "Port 68"


class PremierPrints(Feed):
    class Meta:
        verbose_name = "Premier Prints"
        verbose_name_plural = "Premier Prints"


class Scalamandre(Feed):
    class Meta:
        verbose_name = "Scalamandre"
        verbose_name_plural = "Scalamandre"


class Schumacher(Feed):
    class Meta:
        verbose_name = "Schumacher"
        verbose_name_plural = "Schumacher"


class Seabrook(Feed):
    class Meta:
        verbose_name = "Seabrook"
        verbose_name_plural = "Seabrook"


class Stout(Feed):
    class Meta:
        verbose_name = "Stout"
        verbose_name_plural = "Stout"


class Surya(Feed):
    class Meta:
        verbose_name = "Surya"
        verbose_name_plural = "Surya"


class Tempaper(Feed):
    class Meta:
        verbose_name = "Tempaper"
        verbose_name_plural = "Tempaper"


class York(Feed):
    class Meta:
        verbose_name = "York"
        verbose_name_plural = "York"


class Zoffany(Feed):
    class Meta:
        verbose_name = "Zoffany"
        verbose_name_plural = "Zoffany"
