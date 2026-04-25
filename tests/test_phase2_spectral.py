from pathlib import Path

from shared.instruments.hyperspectral import parse_envi
from shared.instruments.lidar_drone import parse as parse_lidar


def test_lidar_parser_accepts_laz(tmp_path):
    p = tmp_path / 'kwale.laz'
    p.write_text('placeholder')
    out = parse_lidar(str(p))
    assert out.dem_url.startswith('minio://')


def test_hyperspectral_parser_requires_hdr_img(tmp_path):
    hdr = tmp_path / 'kwale.hdr'
    img = tmp_path / 'kwale.img'
    hdr.write_text('ENVI')
    img.write_text('binary')
    out = parse_envi(str(hdr), str(img))
    assert out['bands'] == 281
