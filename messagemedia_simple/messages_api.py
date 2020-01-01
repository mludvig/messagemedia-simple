#!/usr/bin/env python3

from datetime import datetime
import base64
import json
import hmac
import hashlib
import requests

class MessagesAPI:
    def __init__(self, api_key, api_secret, hmac_auth=True, api_host="api.messagemedia.com"):
        self._api_key = api_key
        self._api_secret = api_secret
        self._api_host = api_host
        self._hmac_auth = hmac_auth

        self._override_date = None  # Used for unit testing

    def _auth_headers(self, method, request_path, content=None):
        if self._hmac_auth:
            return self._auth_headers_hmac(method, request_path, content)
        return self._auth_headers_basic(method, request_path)

    def _auth_headers_basic(self, method, request_path):    # pylint: disable=unused-argument
        headers = {}
        auth_str = base64.b64encode(f"{self._api_key}:{self._api_secret}".encode("ascii")).decode("ascii")
        headers["Authorization"] = f"Basic {auth_str}"
        return headers

    def _auth_headers_hmac(self, method, request_path, content=None):
        headers = {}
        headers_sequence = []
        auth_data = []

        # Add Date header
        if self._override_date is None:
            now = datetime.utcnow()
            headers["Date"] = datetime.strftime(now, "%a, %d %b %Y %H:%M:%S GMT")
        else:
            headers["Date"] = self._override_date
        headers_sequence.append("Date")
        auth_data.append(f"Date: {headers['Date']}")

        # Add Content-MD5 header if present
        if content is not None:
            content_md5 = hashlib.md5(content).hexdigest()
            headers["x-Content-MD5"] = content_md5
            headers_sequence.append("x-Content-MD5")
            auth_data.append(f"x-Content-MD5: {headers['x-Content-MD5']}")

        # Add request line
        auth_data.append(f"{method} {request_path} HTTP/1.1")
        headers_sequence.append("request-line")

        # Calculate signature
        auth_str = "\n".join(auth_data).encode("utf-8")
        signature = hmac.HMAC(self._api_secret.encode("ascii"), auth_str, hashlib.sha1).digest()
        signature_b64 = base64.b64encode(signature).decode("ascii")

        # Add Authorization header
        headers_str = " ".join(headers_sequence)
        headers["Authorization"] = f'hmac username="{self._api_key}", algorithm="hmac-sha1", headers="{headers_str}", signature="{signature_b64}"'

        return headers

    def _make_api_call(self, method, api_path, payload=None):
        headers = self._auth_headers(method, api_path, payload)
        headers["Accept"] = "application/json"
        if payload is not None:
            headers["Content-Type"] = "application/json"

        if method == "GET":
            response = requests.get(f"https://{self._api_host}{api_path}", headers=headers,)
        elif method == "POST":
            response = requests.post(f"https://{self._api_host}{api_path}", headers=headers, data=payload,)
        else:
            raise NotImplementedError(f"HTTP method '{method}' is not implemented")

        # If request wasn't successful - raise Exception
        # The exception will have e.response and e.request set
        response.raise_for_status()

        return response

    def send_message(self, content, destination_number, delivery_report=True, message_format="SMS", **kwargs):
        api_path = "/v1/messages"
        message = {}
        message["content"] = content
        message["destination_number"] = destination_number
        message["delivery_report"] = delivery_report
        message["format"] = message_format
        message.update(**kwargs)

        payload = json.dumps({"messages": [message]}).encode("ascii")
        response = self._make_api_call("POST", api_path, payload)

        return response.json()

    def get_message_status(self, message_id):
        api_path = f"/v1/messages/{message_id}"

        response = self._make_api_call("GET", api_path)

        return response.json()

    def get_replies(self):
        api_path = f"/v1/replies"

        response = self._make_api_call("GET", api_path)

        return response.json()

    def confirm_replies(self, reply_ids):
        api_path = "/v1/replies/confirmed"
        if not isinstance(reply_ids, list):
            reply_ids = [reply_ids]

        payload = json.dumps({"reply_ids": reply_ids}).encode("ascii")
        response = self._make_api_call("POST", api_path, payload)

        return response.ok

    def get_delivery_reports(self):
        api_path = f"/v1/delivery_reports"

        response = self._make_api_call("GET", api_path)

        return response.json()

    def confirm_delivery_reports(self, delivery_report_ids):
        api_path = "/v1/delivery_reports/confirmed"
        if not isinstance(delivery_report_ids, list):
            delivery_report_ids = [delivery_report_ids]

        payload = json.dumps({"delivery_report_ids": delivery_report_ids}).encode("ascii")
        response = self._make_api_call("POST", api_path, payload)

        return response.ok
