"""HTTP requests without implicit local credentials or environment proxies."""
import requests


def session():
    client = requests.Session()
    client.trust_env = False
    return client


def get(url, **kwargs):
    with session() as client:
        return client.get(url, **kwargs)
