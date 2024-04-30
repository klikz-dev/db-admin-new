from django.core.management.base import BaseCommand

import os
import glob
import environ

from vendor.models import Sync
from monitor.models import Log

env = environ.Env()

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"


class Command(BaseCommand):
    help = f"Migrate Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()

        if "cleanup-images" in options['functions']:
            processor.cleanupImages()

        if "cleanup-logs" in options['functions']:
            processor.cleanupLogs()


class Processor:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def cleanupImages(self):
        # Empty Image folders
        imageFolders = ["thumbnail", "roomset", "hires", "compressed"]
        for imageFolder in imageFolders:
            for file in glob.glob(f"{FILEDIR}/images/{imageFolder}/*.*"):
                os.remove(file)

    def cleanupLogs(self):
        # Empty Logs
        Log.objects.all().delete()
