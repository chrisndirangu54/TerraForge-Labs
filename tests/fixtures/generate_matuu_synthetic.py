from __future__ import annotations

import json
import random
from pathlib import Path


def generate(path: str = "tests/fixtures/matuu_synthetic.geojson") -> None:
    random.seed(42)
    n = 80
    features = []
    for i in range(n):
        lon = random.uniform(37.45, 37.55)
        lat = random.uniform(-1.20, -1.10)
        ta = max(1.0, random.lognormvariate(4.7, 0.6))
        nb = ta * random.uniform(4, 8)
        sn = max(1.0, random.lognormvariate(3.8, 0.8))
        err = random.uniform(5, 15)
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "sample_id": f"MTU-{i:03d}",
                    "elevation_m": random.uniform(950, 1200),
                    "ta_ppm": ta,
                    "nb_ppm": nb,
                    "sn_ppm": sn,
                    "fe_ppm": random.uniform(1000, 80000),
                    "susceptibility_si": random.lognormvariate(-5, 0.8),
                    "ph": max(5.0, min(8.5, random.gauss(6.2, 0.4))),
                    "conductivity_us_cm": random.lognormvariate(5.0, 0.5),
                    "assay_error_pct": err,
                },
            }
        )

    # flag ~15% high-error
    for idx in random.sample(range(n), 12):
        features[idx]["properties"]["assay_error_pct"] = random.uniform(20, 30)

    geojson = {"type": "FeatureCollection", "features": features}
    Path(path).write_text(json.dumps(geojson), encoding="utf-8")


if __name__ == "__main__":
    generate()
