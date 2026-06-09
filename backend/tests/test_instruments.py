from pathlib import Path


def test_sem_parser_protocol_stub_exists():
    source = Path("shared/instruments/sem_zeiss_jeol.py").read_text()
    assert "class SEMParser(Protocol)" in source
    assert "def segment_phases" in source


def test_required_instrument_modules_exist():
    required = [
        "xrf_bruker.py",
        "xrf_olympus.py",
        "terrameter.py",
        "petrographic.py",
        "eds_oxford.py",
    ]
    base = Path("shared/instruments")
    for name in required:
        assert (base / name).exists()
