from django.contrib.gis.db import models


class Dataset(models.Model):
    SCHEMA_TYPES = (
        ("observation", "Observation"),
        ("drillhole", "Drillhole"),
        ("assay", "Assay"),
        ("artifact", "Artifact"),
    )

    name = models.CharField(max_length=255)
    project_id = models.UUIDField(null=True, blank=True)
    schema_type = models.CharField(max_length=32, choices=SCHEMA_TYPES, default="observation")
    source = models.CharField(max_length=100, default="marketplace")
    parser_version = models.CharField(max_length=100, default="unknown@0.0.0")
    crs = models.CharField(max_length=32, default="EPSG:4326")
    geom = models.GeometryField(null=True, blank=True)
    image_field = models.JSONField(null=True, blank=True)
    petro_ppl_image = models.ImageField(upload_to="petro/", null=True, blank=True)
    petro_xpl_image = models.ImageField(upload_to="petro/", null=True, blank=True)
    sem_se_image = models.ImageField(upload_to="sem/", null=True, blank=True)
    sem_bse_image = models.ImageField(upload_to="sem/", null=True, blank=True)
    sem_eds_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)