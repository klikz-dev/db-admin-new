import environ
from vendor.models import Product, Sync
from utils import debug, const

env = environ.Env()


class Shopify:
    def __init__(self, brand, Feed):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
