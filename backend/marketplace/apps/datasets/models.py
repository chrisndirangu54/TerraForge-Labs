from django.contrib.gis.db import models


class Dataset(models.Model):
    name = models.CharField(max_length=255)
    geom = models.GeometryField(null=True, blank=True)
    image_field = models.JSONField(null=True, blank=True)
    petro_ppl_image = models.ImageField(upload_to="petro/", null=True, blank=True)
    petro_xpl_image = models.ImageField(upload_to="petro/", null=True, blank=True)
    sem_se_image = models.ImageField(upload_to="sem/", null=True, blank=True)
    sem_bse_image = models.ImageField(upload_to="sem/", null=True, blank=True)
    sem_eds_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
