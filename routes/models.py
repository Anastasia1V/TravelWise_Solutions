from django.db import models
from django.conf import settings


class Route(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    details = models.JSONField(default=list, blank=True)
    created = models.DateTimeField(auto_now_add=True)