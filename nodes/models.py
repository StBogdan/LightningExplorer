from django.db import models

# Create your models here.
class Metric(models.Model):
    image_url = models.CharField(max_length=50)
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=250)
