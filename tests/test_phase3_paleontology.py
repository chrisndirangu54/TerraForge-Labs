from backend.processing.paleontology import fossil_occurrences, heritage_risk


def test_paleontology_occurrences_and_risk():
    occ = fossil_occurrences([35, 2, 37, 4])
    risk = heritage_risk({})
    assert occ['type'] == 'FeatureCollection'
    assert risk['heritage_risk'] in {'low', 'medium', 'high', 'critical'}
