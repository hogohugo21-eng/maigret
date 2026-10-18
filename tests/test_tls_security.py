"""Exercise certificate validation with real, local HTTPS handshakes."""
import ssl
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import trustme
from aiohttp import web, ClientConnectorCertificateError

from maigret.checking import SimpleAiohttpChecker
from maigret.submit import Submitter


@pytest.mark.parametrize('client_kind', ['checker', 'submitter'])
@pytest.mark.parametrize('certificate', ['valid', 'untrusted', 'wrong_host', 'expired'])
async def test_https_authenticates_server(monkeypatch, client_kind, certificate):
    for name in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy'):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv('NO_PROXY', '*')
    ca = trustme.CA()
    kwargs = {}
    if certificate == 'expired':
        kwargs = dict(not_before=datetime(2000, 1, 1, tzinfo=timezone.utc),
                      not_after=datetime(2001, 1, 1, tzinfo=timezone.utc))
    cert = ca.issue_cert('wrong.example' if certificate == 'wrong_host' else '127.0.0.1', **kwargs)
    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    cert.configure_cert(server_context)
    original_context = ssl.create_default_context

    def client_context(*args, **kwargs):
        context = original_context(*args, **kwargs)
        if certificate != 'untrusted':
            ca.configure_trust(context)
        return context

    monkeypatch.setattr(ssl, 'create_default_context', client_context)
    hits = []

    async def profile(request):
        hits.append(request.path)
        return web.Response(text='profile')

    app = web.Application()
    app.router.add_get('/', profile)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 0, ssl_context=server_context)
    await site.start()
    url = f'https://127.0.0.1:{runner.addresses[0][1]}/'
    try:
        if client_kind == 'checker':
            checker = SimpleAiohttpChecker()
            checker.prepare(url, timeout=5)
            body, status, error = await checker.check()
            if certificate == 'valid':
                assert (body, status, error) == ('profile', 200, None)
            else:
                assert error is not None
                assert status == 0
        else:
            submitter = Submitter(Mock(), Mock(), Mock(), SimpleNamespace(proxy=None, cookie_file=None))
            try:
                if certificate == 'valid':
                    async with submitter.session.get(url) as response:
                        assert await response.text() == 'profile'
                else:
                    with pytest.raises(ClientConnectorCertificateError):
                        await submitter.session.get(url)
            finally:
                await submitter.close()
        assert hits == (['/'] if certificate == 'valid' else [])
    finally:
        await runner.cleanup()
