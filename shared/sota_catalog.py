"""Catalog of pretrained SOTA models and open geoscience datasets."""

from __future__ import annotations

SOTA_PRETRAINED_MODELS = {
    "torchvision-resnet18": {
        "provider": "torchvision",
        "weights": "IMAGENET1K_V1",
        "feature_dim": 512,
        "task": "image_classification_features",
    },
    "torchvision-efficientnet-b0": {
        "provider": "torchvision",
        "weights": "IMAGENET1K_V1",
        "feature_dim": 1280,
        "task": "image_classification_features",
    },
    "text-embedding-004": {
        "provider": "google_gemini",
        "feature_dim": 768,
        "task": "text_embedding",
    },
    "hash-embedding-fallback": {
        "provider": "terraforge",
        "feature_dim": 768,
        "task": "text_embedding",
    },
}

SOTA_DATASETS = {
    "matuu_field_geochem": {
        "source": "tests/fixtures/matuu_synthetic.geojson",
        "type": "field_geochemistry",
        "region": "Kenya-Matuu",
    },
    "gbif_kenya_metallophytes": {
        "source": "data/geobotany/gbif_kenya_metallophytes.json",
        "api": "https://api.gbif.org/v1/occurrence/search",
        "type": "species_occurrence",
    },
    "inaturalist_kenya_plants": {
        "source": "data/geobotany/inaturalist_kenya_plants.json",
        "api": "https://api.inaturalist.org/v1/observations",
        "type": "research_grade_observations",
    },
    "usgs_mineral_signatures": {
        "source": "data/sota/usgs_mineral_signatures.json",
        "reference": "USGS Spectral Library v7 (subset)",
        "type": "spectral_prototypes",
    },
    "imagenet1k_pretrain": {
        "source": "torchvision://IMAGENET1K_V1",
        "type": "pretrained_backbone",
    },
}