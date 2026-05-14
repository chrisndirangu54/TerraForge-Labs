from __future__ import annotations

MAP_MODES = [
    "2d_street",
    "2d_satellite",
    "2d_hybrid",
    "3d_terrain",
    "3d_geological",
    "google_satellite",
    "google_photorealistic_3d",
]

LAYER_GROUPS = {
    "geological": [
        "kriging_grade_heatmap",
        "deposit_model_mesh",
        "drillhole_traces",
        "sample_points",
        "structural_measurements",
        "geophysical_sections",
        "tectonic_faults",
        "satellite_spectral_indices",
        "outcrop_classification",
        "historical_boreholes",
    ],
    "hydrogeology": [
        "groundwater_table_surface",
        "aquifer_zones",
        "borehole_water_levels",
        "recharge_zones",
        "contamination_plumes",
    ],
    "urban_infrastructure": [
        "settlement_boundaries",
        "building_footprints",
        "roads_tracks",
        "utilities",
        "land_use_zoning",
        "infrastructure_assets",
    ],
    "environmental": [
        "insar_deformation",
        "heritage_sensitivity",
        "illegal_mining_detections",
        "nema_compliance_zones",
    ],
    "satellite_feeds": ["sentinel2_rgb", "sar_intensity", "thermal"],
}

GOOGLE_MAPS_FREE_EVENTS = {
    "essentials": 10_000,
    "pro": 5_000,
    "enterprise": 1_000,
}


def map_provider_plan(use_google: bool = False) -> dict:
    if not use_google:
        return {
            "provider": "open_source",
            "vector_tiles": "MapLibre GL JS + OpenFreeMap",
            "mobile": "MapLibre Native",
            "offline": "PMTiles",
            "estimated_monthly_cost_usd": 0,
        }
    return {
        "provider": "google_premium_addon",
        "satellite_tiles": "Google Maps Tile API",
        "photorealistic_3d": "Google Photorealistic 3D Tiles",
        "free_events": GOOGLE_MAPS_FREE_EVENTS,
        "estimated_monthly_cost_usd": 1200,
    }


def offline_pack_manifest(country: str, include_satellite: bool = True) -> dict:
    slug = country.lower().replace(" ", "_")
    packs = [
        {
            "name": f"{slug}_osm.pmtiles",
            "type": "osm_vector",
            "zoom_range": "z0-z14",
            "estimated_size_mb": 800,
        }
    ]
    if include_satellite:
        packs.append(
            {
                "name": f"{slug}_satellite.pmtiles",
                "type": "sentinel2_rgb_mosaic",
                "zoom_range": "z0-z12",
                "estimated_size_mb": 2048,
            }
        )
    return {
        "country": country,
        "format": "PMTiles",
        "packs": packs,
        "offline_ready": True,
    }


def cesium_tileset_job(job_id: str, source_obj_url: str) -> dict:
    return {
        "job_id": job_id,
        "pipeline": ["GemPy OBJ", "obj2gltf", "py3dtiles", "MinIO tileset"],
        "source_obj_url": source_obj_url,
        "tileset_url": f"minio://deposit-models/{job_id}/tileset.json",
        "style_attribute": "ta_ppm",
    }


def layer_catalogue() -> dict:
    return {"map_modes": MAP_MODES, "layer_groups": LAYER_GROUPS}
