from __future__ import annotations

from fastapi import APIRouter, Query

from backend.api.services.response_display import enrich_response

SEED_ITEMS = [
    {
        "id": "plugin-aseg-gdf2",
        "name": "ASEG-GDF2 parser plugin",
        "description": "Import ASEG-GDF2 geophysics exports into capture pipeline",
        "price_usd": 0,
        "category": "plugin",
        "formats": ["gdf2"],
    },
    {
        "id": "plugin-geosoft-grd",
        "name": "Geosoft .grd parser plugin",
        "description": "Grid import for aeromag and radiometrics workflows",
        "price_usd": 0,
        "category": "plugin",
        "formats": ["grd"],
    },
    {
        "id": "plugin-las-laz",
        "name": "LiDAR LAS/LAZ importer",
        "description": "Point cloud ingest with DTM and lineament extraction",
        "price_usd": 19,
        "category": "plugin",
        "formats": ["las", "laz"],
    },
    {
        "id": "report-jorc-template",
        "name": "JORC 2012 report template",
        "description": "Table 1 checklist, resource tables, and disclaimer workflow",
        "price_usd": 49,
        "category": "report",
        "formats": ["docx", "pdf"],
    },
    {
        "id": "report-ni43101",
        "name": "NI 43-101 template",
        "description": "Canadian disclosure sections with assay QA/QC annex",
        "price_usd": 49,
        "category": "report",
        "formats": ["docx"],
    },
    {
        "id": "report-evidence-bundle",
        "name": "Investor evidence bundle",
        "description": "JORC + kriging + financial snapshot export pack",
        "price_usd": 79,
        "category": "report",
        "formats": ["zip", "pdf"],
    },
    {
        "id": "drill-matuu-fence",
        "name": "Matuu scout drill fence (LAS)",
        "description": "12-hole RC fence with assay, lithology, and survey tables",
        "price_usd": 0,
        "category": "drill_log",
        "formats": ["csv", "las"],
        "holes": 12,
        "total_metres": 1840,
    },
    {
        "id": "drill-kitui-infill",
        "name": "Kitui infill drill program",
        "description": "8 diamond holes with downhole gamma and structure logs",
        "price_usd": 29,
        "category": "drill_log",
        "formats": ["csv", "xlsx"],
        "holes": 8,
        "total_metres": 1260,
    },
    {
        "id": "drill-demo-collars",
        "name": "Demo collar & survey pack",
        "description": "Collar, survey, assay, and lithology CSV bundle for QA/QC demos",
        "price_usd": 0,
        "category": "drill_log",
        "formats": ["csv"],
        "holes": 6,
        "total_metres": 720,
    },
    {
        "id": "dataset-mrds-kenya",
        "name": "USGS MRDS Kenya bundle",
        "description": "Historical occurrences and deposit references for Kenya",
        "price_usd": 0,
        "category": "dataset",
        "formats": ["geojson", "csv"],
    },
    {
        "id": "template-kenya-el",
        "name": "Kenya EL progress template",
        "description": "Exploration licence milestone tracker with NEMA hooks",
        "price_usd": 29,
        "category": "report",
        "formats": ["xlsx"],
    },
]

DRILL_LOG_PREVIEW = [
    {
        "hole_id": "MAT-DD-001",
        "easting": 372450,
        "northing": 9871200,
        "depth_m": 150,
        "dip": -60,
        "azimuth": 225,
        "mean_ta_ppm": 118,
        "lithology": "pegmatite",
    },
    {
        "hole_id": "MAT-DD-002",
        "easting": 372520,
        "northing": 9871250,
        "depth_m": 180,
        "dip": -58,
        "azimuth": 220,
        "mean_ta_ppm": 142,
        "lithology": "pegmatite",
    },
    {
        "hole_id": "MAT-RC-003",
        "easting": 372610,
        "northing": 9871180,
        "depth_m": 120,
        "dip": -55,
        "azimuth": 215,
        "mean_ta_ppm": 96,
        "lithology": "saprolite",
    },
    {
        "hole_id": "MAT-RC-004",
        "easting": 372690,
        "northing": 9871300,
        "depth_m": 140,
        "dip": -57,
        "azimuth": 218,
        "mean_ta_ppm": 131,
        "lithology": "pegmatite",
    },
]

router = APIRouter()


@router.get("/marketplace/catalogue")
async def catalogue(category: str | None = Query(default=None)) -> dict:
    items = SEED_ITEMS
    if category:
        items = [item for item in SEED_ITEMS if item["category"] == category]
    categories = sorted({item["category"] for item in SEED_ITEMS})
    return enrich_response(
        {
            "items": items,
            "count": len(items),
            "categories": categories,
            "drill_log_preview": DRILL_LOG_PREVIEW,
        }
    )