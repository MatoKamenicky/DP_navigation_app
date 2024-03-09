from django.contrib.gis.db import models

class Coordinates(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
