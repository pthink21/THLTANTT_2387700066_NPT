"""Bounded HTTP access to the explicitly created lab target only."""
import time
from urllib.parse import urlsplit, urlunsplit
import requests


class LabHTTP:
    def __init__(self, port=5102):
        self.port = port
        self.session = requests.Session()
        self.session.trust_env = False

    def validate(self, url):
        p = urlsplit(url)
        if (p.scheme != 'http' or p.hostname != '127.0.0.1'
                or p.port != self.port or p.username or p.password):
            raise ValueError(f'Chỉ cho phép http://127.0.0.1:{self.port} trong lab này')
        return urlunsplit((p.scheme, p.netloc, p.path or '/', p.query, ''))

    def get(self, url, **kwargs):
        url = self.validate(url)
        time.sleep(0.025)
        with self.session.get(url, timeout=(2, 3), allow_redirects=False,
                              stream=True, **kwargs) as response:
            if 300 <= response.status_code < 400:
                raise ValueError('Redirect bị chặn; chưa quét URL đích')
            response.raise_for_status()
            chunks, size = [], 0
            for chunk in response.iter_content(16384):
                size += len(chunk)
                if size > 512_000:
                    raise ValueError('Response vượt giới hạn 512 KB')
                chunks.append(chunk)
            response._content = b''.join(chunks)
            return response
