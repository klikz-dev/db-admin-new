from django.db import models


class Log(models.Model):
    class Meta:
        verbose_name = "Log"
        verbose_name_plural = "Logs"

    source = models.CharField(max_length=200)

    type = models.CharField(max_length=200, default="Info")
    message = models.CharField(max_length=2000)

    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} - {}".format(self.source, self.date)
