"""Reject browser requests that can change local settings from another site."""
import pytest
from maigret.web.app import app


@pytest.mark.parametrize('headers', [
    {'Origin': 'https://attacker.example'},
    {'Origin': 'null'},
    {'Referer': 'https://attacker.example/form'},
    {'Sec-Fetch-Site': 'cross-site'},
])
def test_cross_origin_settings_rejected(tmp_path, monkeypatch, headers):
    settings = tmp_path / 'settings.json'
    monkeypatch.setitem(app.config, 'SETTINGS_FILE', str(settings))
    with app.test_client() as client:
        response = client.post('/settings', data={'proxy': 'http://attacker.example:8080'}, headers=headers)
    assert response.status_code == 403
    assert not settings.exists()


def test_same_origin_settings_allowed(tmp_path, monkeypatch):
    settings = tmp_path / 'settings.json'
    monkeypatch.setitem(app.config, 'SETTINGS_FILE', str(settings))
    with app.test_client() as client:
        response = client.post('/settings', data={'timeout': '10'}, headers={'Origin': 'http://localhost'})
    assert response.status_code == 302
    assert settings.exists()
