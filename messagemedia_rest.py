#!/usr/bin/env python3

from datetime import datetime
import base64
import hmac
import hashlib
import requests

class MessageMediaREST:
    def __init__(self, api_key, api_secret):
        self._api_key = api_key
        self._api_secret = api_secret

    def _build_auth(self, method, request_path, content_md5 = None):
        headers = {}
        headers_sequence = []
        auth_data = []

        # Add Date header
        now = datetime.utcnow()
        headers["Date"] = datetime.strftime(now, "%a, %-d %b %Y %H:%M:%S GMT")
        headers_sequence.append("Date")
        auth_data.append(f"Date: {headers['Date']}")

        # Add Content-MD5 header if present
        if content_md5 is not None:
            headers["Content-MD5"] = content_md5
            headers_sequence.append("Content-MD5")
            auth_data.append(f"Content-MD5: {headers['Content-MD5']}")

        # Add request line
        auth_data.append(f"{method} {request_path} HTTP/1.1")
        headers_sequence.append("request_line")

        # Calculate signature
        auth_str = "\n".join(auth_data).encode('utf-8')
        signature = hmac.HMAC(self._api_secret.encode('ascii'), auth_str, hashlib.sha1).digest()
        signature_b64 = base64.b64encode(signature).decode('ascii')

        # Add Authorization header
        headers_str = " ".join(headers_sequence)
        headers["Authorization"] = f'hmac username="{self._api_key}", algorithm="hmac-sha1", headers="{headers_str}", signature="{signature_b64}"'

        return headers

if __name__ == "__main__":
    mm = MessageMediaREST("API_KEY_12345678", "API_SECRET_12345678")
    print(mm._build_auth("GET", "/v1/", "bc29bec61ba97d2092e9aebecf8ef744"))
