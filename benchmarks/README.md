# TerraForge Benchmarks

Nightly model evaluation harness for core ML scaffolds.

## Suites

| Suite | Module | Metrics |
|-------|--------|---------|
| Mineral classifier | `models.mineral_classifier.evaluate` | accuracy, f1_macro |
| Geobotany classifier | `models.geobotany_classifier.evaluate` | top1_accuracy, top3_accuracy, inference_ms_android |
| Grain segmentation | `models.grain_segmentation.evaluate` | mean_iou, modal_error_pct |

## Run locally

```bash
poetry run python benchmarks/run_all.py
```

Output is JSON written to stdout with a UTC timestamp and per-suite metrics.

## CI

- **Smoke test:** `poetry run pytest backend/tests/test_benchmarks.py`
- **Nightly:** `.github/workflows/benchmark.yml` runs `benchmarks/run_all.py` on schedule