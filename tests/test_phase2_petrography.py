from shared.instruments.raman import parse_raman
from shared.instruments.xrd_bruker import parse_xrd


def test_xrd_parser_returns_phases(tmp_path):
    f = tmp_path / 'sample.raw'
    f.write_text('xrd')
    out = parse_xrd(str(f))
    assert len(out['mineral_phases']) >= 3


def test_raman_parser_returns_peak_table():
    out = parse_raman('sample.spc')
    assert out['peak_table']
