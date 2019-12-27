from datetime import datetime

import pytest
import responses

from messagemedia_simple import MessageMediaREST

API_KEY = "API_KEY_12345678"
API_SECRET = "API_SECRET_12345678"


def test_basic_auth():
    mm = MessageMediaREST(API_KEY, API_SECRET, hmac_auth=False)
    response = mm._auth_headers("GET", "/v1")
    expected_auth = "Basic QVBJX0tFWV8xMjM0NTY3ODpBUElfU0VDUkVUXzEyMzQ1Njc4"
    assert response["Authorization"] == expected_auth


def test_hmac_auth_without_content():
    mm = MessageMediaREST(API_KEY, API_SECRET)
    response = mm._auth_headers("GET", "/v1")
    assert response["Date"]
    assert response["Authorization"]


def test_hmac_auth_with_content():
    mm = MessageMediaREST(API_KEY, API_SECRET)
    content = '{ "something": "Test test test" }'
    response = mm._auth_headers("GET", "/v1", content.encode("ascii"))
    assert response["Date"]
    assert response["x-Content-MD5"]
    assert response["Authorization"]
    # Check that the date is at most 2 seconds ago
    date = datetime.strptime(response["Date"], "%a, %d %b %Y %H:%M:%S GMT")
    max_delta = 2
    assert date.timestamp() > datetime.utcnow().timestamp() - max_delta


def test_hmac_auth_without_content_set_date():
    mm = MessageMediaREST(API_KEY, API_SECRET)
    date = "Thu, 12 Dec 2019 10:16:19 GMT"
    response = mm._auth_headers("GET", "/v1", _override_date=date)
    assert response["Date"] == date
    assert (
        response["Authorization"]
        == 'hmac username="API_KEY_12345678", algorithm="hmac-sha1", headers="Date request-line", signature="GXoYmlLRdJSmIMbeM8YfL+ngCnY="'
    )


def test_hmac_auth_with_content_set_date():
    mm = MessageMediaREST(API_KEY, API_SECRET)
    content = '{ "something": "Test test test" }'
    date = "Thu, 12 Dec 2019 10:16:19 GMT"
    response = mm._auth_headers("GET", "/v1", content.encode("ascii"), _override_date=date)
    assert response["Date"] == date
    assert response["x-Content-MD5"] == "9388bdde7687be0933cc1a68cc44a6b1"
    assert (
        response["Authorization"]
        == 'hmac username="API_KEY_12345678", algorithm="hmac-sha1", headers="Date x-Content-MD5 request-line", signature="4s+H5SQr4Ucc5dAHO/KdJ1RDj0k="'
    )
