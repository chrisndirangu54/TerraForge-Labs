from shared.instruments.terrameter import TerrameterParser


def test_parse_flag_and_invert():
    parser = TerrameterParser()
    rows = parser.parse("tests/fixtures/sample_terrameter.xml")
    assert len(rows) == 2
    assert rows[1]["flagged"] is True

    inv = parser.invert_1d(rows, n_layers=4)
    assert len(inv) == 4
    assert inv[0]["depth_m"] > 0
