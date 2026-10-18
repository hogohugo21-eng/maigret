from unittest.mock import Mock

import pytest
from yarl import URL

from maigret.activation import import_aiohttp_cookies
from maigret.checking import SimpleAiohttpChecker
from maigret.db_updater import _fetch_meta
from maigret.report import generate_report_template
from maigret.web.app import app


@pytest.mark.parametrize('target', ['http://example.com/', 'https://sub.example.com/'])
async def test_imported_secure_host_cookie_is_not_disclosed(tmp_path, target):
    filename = tmp_path / 'cookies.txt'
    filename.write_text('# Netscape HTTP Cookie File\nexample.com\tFALSE\t/\tTRUE\t2147483647\tsession\tSECRET\n')
    jar = import_aiohttp_cookies(str(filename))
    assert 'session' in jar.filter_cookies(URL('https://example.com/'))
    assert 'session' not in jar.filter_cookies(URL(target))


async def test_expired_cookie_is_not_revived(tmp_path):
    filename = tmp_path / 'cookies.txt'
    filename.write_text('# Netscape HTTP Cookie File\n.example.com\tTRUE\t/\tTRUE\t1\tsession\tEXPIRED\n')
    assert not list(import_aiohttp_cookies(str(filename)))


@pytest.mark.parametrize('client', ['checker', 'database'])
async def test_local_netrc_is_not_sent(tmp_path, monkeypatch, httpserver, client):
    netrc = tmp_path / 'netrc'
    netrc.write_text('machine localhost login PRIVATE_USER password PRIVATE_PASSWORD\n')
    monkeypatch.setenv('NETRC', str(netrc))
    monkeypatch.setenv('NO_PROXY', '*')
    seen = []
    from werkzeug.wrappers import Response

    def handler(request):
        seen.append(request.headers.get('Authorization'))
        return Response('{}', content_type='application/json')

    httpserver.expect_request('/').respond_with_handler(handler)
    url = httpserver.url_for('/').replace('127.0.0.1', 'localhost')
    if client == 'checker':
        checker = SimpleAiohttpChecker(logger=Mock())
        checker.prepare(url, timeout=5)
        _, status, error = await checker.check()
        assert status == 200 and error is None
    else:
        assert _fetch_meta(url) == {}
    assert seen == [None]


def test_web_rejects_foreign_host():
    with app.test_client() as client:
        assert client.get('/', headers={'Host': 'attacker.example'}).status_code == 400


def test_html_report_has_no_automatic_remote_resources():
    template, _ = generate_report_template(False)
    rendered = template.render(username='test', results=[], supposed_data={})
    from html.parser import HTMLParser

    class Resources(HTMLParser):
        def handle_starttag(self, tag, attrs):
            for key, value in attrs:
                if key == 'src' or (tag == 'link' and key == 'href'):
                    assert not value.startswith(('http:', 'https:', '//'))

    Resources().feed(rendered)
