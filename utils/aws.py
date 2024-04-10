import os
import environ
import requests
import json
import boto3

from utils import debug, common
from vendor.models import Sync

env = environ.Env()
AWS_ACCESS = env('AWS_ACCESS')
AWS_SECRET = env('AWS_SECRET')

PROCESS = "AWS"


class AWSManager:
    def __init__(self, product=None, thread=None):

        self.s3 = boto3.client(
            's3',
            aws_access_key_id=env('AWS_ACCESS'),
            aws_secret_access_key=env('AWS_SECRET')
        )

        self.imageBucket = "dbproductimages"
        self.feedBucket = "decoratorsbestimages"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def uploadFile(self, src, dst, contentType=None):
        if contentType:
            args = {'ContentType': contentType, 'ACL': 'public-read'}
        else:
            args = {'ACL': 'public-read'}

        self.s3.upload_file(src, self.imageBucket, dst, ExtraArgs=args)

        return f"https://s3.amazonaws.com/{self.imageBucket}/{dst}"
