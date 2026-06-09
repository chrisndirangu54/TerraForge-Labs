from __future__ import annotations

GEOBOTANY_CLASSES = [
    # Obligate copper indicators
    "ocimum_centraliafricanum",
    "haumaniastrum_katangense",
    "haumaniastrum_robertii",
    "becium_centraliafricanum",
    "aeolanthus_biformifolius",
    "commelina_zigzag",
    # Cobalt indicators
    "silene_cobalticola",
    "crotalaria_cobalticola",
    # Nickel / serpentine
    "senecio_coronatus",
    "pearsonia_metallifera",
    # Geothermal / lithological indicators
    "gypsophila_patrinii",
    "euphorbia_quinquecostata",
    # Lead / zinc and export-market metallophytes
    "minuartia_verna",
    "thlaspi_caerulescens",
    "viola_calaminaria",
    "armeria_maritima",
    # Additional African field targets / negative indicators
    "pityrogramma_calomelanos",
    "equisetum_species",
    "tamarix_species",
    "panicum_maximum",
    # Non-indicator classes
    "healthy_grass",
    "acacia_shrub",
    "miombo_tree",
    "bare_soil",
    "unknown_vegetation",
]

INDICATOR_MINERAL_AFFINITY = {
    "ocimum_centraliafricanum": {"Cu": "VERY_HIGH", "Ni": "HIGH"},
    "haumaniastrum_katangense": {"Cu": "HIGH", "Co": "MEDIUM"},
    "haumaniastrum_robertii": {"Cu": "HIGH", "Co": "HIGH"},
    "becium_centraliafricanum": {"Cu": "HIGH", "Co": "HIGH"},
    "aeolanthus_biformifolius": {"Cu": "HIGH"},
    "commelina_zigzag": {"Cu": "MEDIUM"},
    "silene_cobalticola": {"Co": "VERY_HIGH"},
    "crotalaria_cobalticola": {"Co": "HIGH"},
    "senecio_coronatus": {"Ni": "HIGH", "Cr": "MEDIUM"},
    "pearsonia_metallifera": {"Cu": "HIGH", "Ni": "HIGH"},
    "gypsophila_patrinii": {"B": "MEDIUM", "Li": "MEDIUM"},
    "euphorbia_quinquecostata": {"basement_outcrop": "MEDIUM"},
    "minuartia_verna": {"Pb": "HIGH", "Zn": "HIGH"},
    "thlaspi_caerulescens": {"Zn": "VERY_HIGH", "Cd": "HIGH"},
    "viola_calaminaria": {"Zn": "HIGH"},
    "armeria_maritima": {"Pb": "MEDIUM", "Zn": "MEDIUM"},
    "pityrogramma_calomelanos": {"Au": "MEDIUM", "As": "MEDIUM"},
    "equisetum_species": {"Au": "LOW", "U": "MEDIUM"},
    "tamarix_species": {"B": "MEDIUM", "salinity": "HIGH"},
    "panicum_maximum": {"negative_indicator": "LOW_FERTILITY_OR_DISTURBANCE"},
}

GEOBOTANY_CONFIDENCE_THRESHOLD = 0.65
GEOBOTANY_MODEL_ASSET = "assets/models/geobotany_classifier_int8.tflite"
GEOBOTANY_MODEL_VERSION = "geobotany-b0-v0.1"
TRAINING_DATA_SOURCES = [
    "iNaturalist research-grade observations",
    "GBIF occurrence downloads",
    "East African Plants Database photo guide",
    "TerraForge consented field photos",
]


def get_affinity(species: str) -> dict[str, str]:
    return INDICATOR_MINERAL_AFFINITY.get(species, {})
