from plugins.base import discover_plugins


def test_plugin_discovery_finds_seed_plugins():
    discovered = discover_plugins('plugins')
    assert 'plugins.aseg_gdf2' in discovered
    assert 'plugins.geosoft_grd' in discovered
