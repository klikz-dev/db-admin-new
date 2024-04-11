import environ
import boto3

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

    def uploadImage(self, src, dst, contentType):
        args = {'ContentType': contentType, 'ACL': 'public-read'}

        self.s3.upload_file(src, self.imageBucket, dst, ExtraArgs=args)

        return f"https://s3.amazonaws.com/{self.imageBucket}/{dst}"

    def uploadFeed(self, src, dst):
        args = {'ACL': 'public-read'}

        self.s3.upload_file(src, self.feedBucket, dst, ExtraArgs=args)

        return f"https://s3.amazonaws.com/{self.feedBucket}/{dst}"
