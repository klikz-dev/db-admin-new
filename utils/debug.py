import environ
from monitor.models import Log
from utils import common

env = environ.Env()


def log(source, msg):
    print(f"INFO ({source}): " + msg[:1000])


def warn(source, msg):
    Log.objects.create(
        source=source,
        type="Warn",
        message=msg[:1000]
    )
    print(f"WARN ({source}): " + msg[:1000])


def error(source, msg):
    Log.objects.create(
        source=source,
        type="Error",
        message=msg[:1000]
    )
    print(f"ERROR ({source}): " + msg[:1000])

    bodyText = f"<h3><strong>Error Source: {source}</strong></h3><p style='color: red;'><strong>{msg[:1000]}</strong></p><br/>"

    common.sendEmail(
        sender="Decoratorsbest Backend",
        recipient=env('ADMIN'),
        subject="Backend Error",
        body=bodyText
    )
