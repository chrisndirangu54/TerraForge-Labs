from marketplace.models import Dataset, Plugin, Template
from marketplace.views import get_catalogue


def test_marketplace_models_construct():
    p = Plugin(name='aseg_gdf2', version='0.1.0', author='terraforge', price_usd=0, category='plugin')
    d = Dataset(name='MRDS Kenya', region='Kenya', format='json', licence='open', price_usd=0)
    t = Template(name='NI43-101', standard='NI_43_101', language='en', preview_pdf_url='minio://preview.pdf')
    assert p.name and d.region and t.standard


def test_catalogue_has_seed_items():
    cat = get_catalogue()
    assert cat['count'] >= 5
