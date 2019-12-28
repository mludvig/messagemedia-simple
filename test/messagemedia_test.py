import json
from datetime import datetime

import responses

from messagemedia_simple import MessageMediaREST

API_KEY = "API_KEY_12345678"
API_SECRET = "API_SECRET_12345678"

# Pre-computed values for authentication validation
KNOWN_DATE = "Thu, 12 Dec 2019 10:16:19 GMT"
KNOWN_CONTENT = '{"messages": [{"content": "Content", "destination_number": "+1234567890", "delivery_report": true, "format": "SMS"}]}'
KNOWN_CONTENT_MD5 = "5fe6c18746c7d300f04f08a1db90ced2"
KNOWN_AUTH_HMAC_WITH_CONTENT = 'hmac username="API_KEY_12345678", algorithm="hmac-sha1", headers="Date x-Content-MD5 request-line", signature="sLAeOwXXix428meq3vhSmwdN2gg="'

def test_basic_auth():
    mm = MessageMediaREST(API_KEY, API_SECRET, hmac_auth=False)
    response = mm._auth_headers("GET", "/v1/messages")
    expected_auth = "Basic QVBJX0tFWV8xMjM0NTY3ODpBUElfU0VDUkVUXzEyMzQ1Njc4"
    assert response["Authorization"] == expected_auth


def test_hmac_auth_without_content():
    mm = MessageMediaREST(API_KEY, API_SECRET)
    response = mm._auth_headers("GET", "/v1/messages")
    assert response["Date"]
    assert response["Authorization"]


def test_hmac_auth_with_content():
    mm = MessageMediaREST(API_KEY, API_SECRET)
    content = KNOWN_CONTENT
    response = mm._auth_headers("POST", "/v1/messages", content.encode("ascii"))
    # Check that all required headers are set but don't check the values
    assert response["Date"]
    assert response["x-Content-MD5"] == KNOWN_CONTENT_MD5
    assert response["Authorization"]
    # Check that the date is at most 2 seconds ago
    date = datetime.strptime(response["Date"], "%a, %d %b %Y %H:%M:%S GMT")
    max_delta = 2
    assert date.timestamp() > datetime.utcnow().timestamp() - max_delta


def test_hmac_auth_without_content_set_date():
    mm = MessageMediaREST(API_KEY, API_SECRET)
    mm._override_date = KNOWN_DATE
    response = mm._auth_headers("GET", "/v1")
    assert response["Date"] == KNOWN_DATE
    assert (
        response["Authorization"]
        == 'hmac username="API_KEY_12345678", algorithm="hmac-sha1", headers="Date request-line", signature="GXoYmlLRdJSmIMbeM8YfL+ngCnY="'
    )


def test_hmac_auth_with_content_set_date():
    mm = MessageMediaREST(API_KEY, API_SECRET)
    mm._override_date = KNOWN_DATE
    content = KNOWN_CONTENT
    response = mm._auth_headers("POST", "/v1/messages", content.encode("ascii"))
    assert response["Date"] == KNOWN_DATE
    assert response["x-Content-MD5"] == KNOWN_CONTENT_MD5
    assert response["Authorization"] == KNOWN_AUTH_HMAC_WITH_CONTENT


@responses.activate
def test_send_message():
    def request_callback(request):
        expected_payload = {'messages': [{'content': 'Content', 'destination_number': '+1234567890', 'delivery_report': True, 'format': 'SMS'}]}
        headers = request.headers
        payload = json.loads(request.body)
        assert headers['Date'] == KNOWN_DATE
        assert headers['Authorization'] == KNOWN_AUTH_HMAC_WITH_CONTENT
        assert payload == expected_payload
        # Return fake "message_id"
        return (200, {}, json.dumps({"message_id": "1234-1234"}))

    responses.add_callback(responses.POST, "https://api.messagemedia.com/v1/messages",
                           callback=request_callback, content_type='application/json')

    mm = MessageMediaREST(API_KEY, API_SECRET)
    mm._override_date = KNOWN_DATE
    response = mm.send_message("Content", "+1234567890")
    # Check that we got the above "message_id"
    assert response["message_id"] == "1234-1234"
