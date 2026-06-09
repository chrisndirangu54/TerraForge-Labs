from pathlib import Path


def test_marketplace_payment_routes_present():
    src = Path('backend/api/routers/marketplace_payments.py').read_text()
    assert "@router.post('/marketplace/checkout')" in src
    assert "@router.post('/marketplace/install')" in src
