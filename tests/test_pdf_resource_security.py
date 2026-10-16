from unittest.mock import patch

from maigret.report import _pdf_report_link_callback, _BLANK_IMAGE_PATH


def test_pdf_cannot_delegate_untrusted_fetches():
    # Checking DNS and then passing the URL to a separate downloader does not
    # constrain that downloader's redirects or subsequent DNS resolution.
    with patch('socket.getaddrinfo', side_effect=AssertionError('No DNS during report rendering')):
        for uri in ('https://public.example/avatar.png', 'http://1.1.1.1/redirect', 'file:///etc/passwd'):
            assert _pdf_report_link_callback(uri, '') == _BLANK_IMAGE_PATH
