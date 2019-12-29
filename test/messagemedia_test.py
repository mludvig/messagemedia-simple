import json
from datetime import datetime

import pytest
import responses

from messagemedia_simple import MessagesAPI

API_KEY = "API_KEY_12345678"
API_SECRET = "API_SECRET_12345678"

# Pre-computed values for authentication validation
KNOWN_DATE = "Thu, 12 Dec 2019 10:16:19 GMT"
KNOWN_CONTENT = '{"messages": [{"content": "Content", "destination_number": "+1234567890", "delivery_report": true, "format": "SMS"}]}'
KNOWN_CONTENT_MD5 = "5fe6c18746c7d300f04f08a1db90ced2"
KNOWN_AUTH_HMAC_WITH_CONTENT = 'hmac username="API_KEY_12345678", algorithm="hmac-sha1", headers="Date x-Content-MD5 request-line", signature="sLAeOwXXix428meq3vhSmwdN2gg="'

def test_basic_auth():
    mm = MessagesAPI(API_KEY, API_SECRET, hmac_auth=False)
    response = mm._auth_headers("GET", "/v1/messages")
    expected_auth = "Basic QVBJX0tFWV8xMjM0NTY3ODpBUElfU0VDUkVUXzEyMzQ1Njc4"
    assert response["Authorization"] == expected_auth


def test_hmac_auth_without_content():
    mm = MessagesAPI(API_KEY, API_SECRET)
    response = mm._auth_headers("GET", "/v1/messages")
    assert response["Date"]
    assert response["Authorization"]


def test_hmac_auth_with_content():
    mm = MessagesAPI(API_KEY, API_SECRET)
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
    mm = MessagesAPI(API_KEY, API_SECRET)
    mm._override_date = KNOWN_DATE
    response = mm._auth_headers("GET", "/v1")
    assert response["Date"] == KNOWN_DATE
    assert (
        response["Authorization"]
        == 'hmac username="API_KEY_12345678", algorithm="hmac-sha1", headers="Date request-line", signature="GXoYmlLRdJSmIMbeM8YfL+ngCnY="'
    )


def test_hmac_auth_with_content_set_date():
    mm = MessagesAPI(API_KEY, API_SECRET)
    mm._override_date = KNOWN_DATE
    content = KNOWN_CONTENT
    response = mm._auth_headers("POST", "/v1/messages", content.encode("ascii"))
    assert response["Date"] == KNOWN_DATE
    assert response["x-Content-MD5"] == KNOWN_CONTENT_MD5
    assert response["Authorization"] == KNOWN_AUTH_HMAC_WITH_CONTENT


def test_make_api_call_invalid_method():
    mm = MessagesAPI(API_KEY, API_SECRET)
    with pytest.raises(NotImplementedError):
        mm._make_api_call("PUT", "/v1/messages")


@responses.activate
def test_send_message():
    path_url = "/v1/messages"

    def request_callback(request):
        expected_payload = {'messages': [
            {'content': 'Content', 'destination_number': '+1234567890', 'delivery_report': True, 'format': 'SMS'}
        ]}
        headers = request.headers
        payload = json.loads(request.body)
        assert headers['Date'] == KNOWN_DATE
        assert headers['Authorization'] == KNOWN_AUTH_HMAC_WITH_CONTENT
        assert payload == expected_payload
        # Return fake "message_id"
        return (200, {}, json.dumps({"message_id": "1234-1234"}))

    responses.add_callback(responses.POST, f"https://api.messagemedia.com{path_url}",
                           callback=request_callback, content_type="application/json")

    mm = MessagesAPI(API_KEY, API_SECRET)
    mm._override_date = KNOWN_DATE
    response = mm.send_message("Content", "+1234567890")

    assert response["message_id"] == "1234-1234"


@responses.activate
def test_get_message_status():
    path_url = "/v1/messages/1234-1234"

    def request_callback(request):
        assert request.method == "GET"
        assert request.path_url == path_url
        return (200, {}, json.dumps({"message_id": "1234-1234", "status": "delivered"}))

    responses.add_callback(responses.GET, f"https://api.messagemedia.com{path_url}",
                           callback=request_callback, content_type="application/json")

    mm = MessagesAPI(API_KEY, API_SECRET)
    response = mm.get_message_status("1234-1234")

    assert response["message_id"] == "1234-1234"
    assert response["status"] == "delivered"


@responses.activate
def test_get_replies():
    path_url = "/v1/replies"

    def request_callback(request):
        assert request.method == "GET"
        assert request.path_url == path_url
        return (200, {}, json.dumps([{"message_id": "1234-1234", "reply_id": "1234-1234-reply"}]))

    responses.add_callback(responses.GET, f"https://api.messagemedia.com{path_url}",
                           callback=request_callback, content_type="application/json")

    mm = MessagesAPI(API_KEY, API_SECRET)
    response = mm.get_replies()
    # Check that we got the above "message_id"
    assert response[0]["message_id"] == "1234-1234"
    assert response[0]["reply_id"] == "1234-1234-reply"


@responses.activate
def test_confirm_replies_single():
    path_url = "/v1/replies/confirmed"

    def request_callback(request):
        expected_payload = { "reply_ids": [ "1234-1234-reply" ] }
        assert request.method == "POST"
        assert request.path_url == path_url
        payload = json.loads(request.body)
        assert payload == expected_payload
        return (200, {}, "")

    responses.add_callback(responses.POST, f"https://api.messagemedia.com{path_url}",
                           callback=request_callback, content_type="application/json")

    mm = MessagesAPI(API_KEY, API_SECRET)
    response = mm.confirm_replies("1234-1234-reply")
    assert response == True     # pylint: disable=singleton-comparison


@responses.activate
def test_confirm_replies_multi():
    path_url = "/v1/replies/confirmed"
    def request_callback(request):
        expected_payload = { "reply_ids": [ "1234-1234-reply", "1234-5678-reply" ] }
        assert request.method == responses.POST
        assert request.path_url == path_url
        payload = json.loads(request.body)
        assert payload == expected_payload
        return (200, {}, "")

    responses.add_callback(responses.POST, f"https://api.messagemedia.com{path_url}",
                           callback=request_callback, content_type="application/json")

    mm = MessagesAPI(API_KEY, API_SECRET)
    response = mm.confirm_replies(["1234-1234-reply", "1234-5678-reply"])
    assert response == True     # pylint: disable=singleton-comparison


@responses.activate
def test_get_delivery_reports():
    path_url = "/v1/delivery_reports"

    def request_callback(request):
        assert request.method == "GET"
        assert request.path_url == path_url
        return (200, {}, json.dumps([{"message_id": "1234-1234", "reply_id": "1234-1234-reply"}]))

    responses.add_callback(responses.GET, f"https://api.messagemedia.com{path_url}",
                           callback=request_callback, content_type="application/json")

    mm = MessagesAPI(API_KEY, API_SECRET)
    response = mm.get_delivery_reports()
    # Check that we got the above "message_id"
    assert response[0]["message_id"] == "1234-1234"
    assert response[0]["reply_id"] == "1234-1234-reply"


@responses.activate
def test_confirm_delivery_reports_single():
    path_url = "/v1/delivery_reports/confirmed"

    def request_callback(request):
        expected_payload = { "delivery_report_ids": [ "1234-1234-delivery" ] }
        assert request.method == "POST"
        assert request.path_url == path_url
        payload = json.loads(request.body)
        assert payload == expected_payload
        return (200, {}, "")

    responses.add_callback(responses.POST, f"https://api.messagemedia.com{path_url}",
                           callback=request_callback, content_type="application/json")

    mm = MessagesAPI(API_KEY, API_SECRET)
    response = mm.confirm_delivery_reports("1234-1234-delivery")
    assert response == True     # pylint: disable=singleton-comparison


@responses.activate
def test_confirm_delivery_reports_multi():
    path_url = "/v1/delivery_reports/confirmed"
    def request_callback(request):
        expected_payload = { "delivery_report_ids": [ "1234-1234-delivery", "1234-5678-delivery" ] }
        assert request.method == responses.POST
        assert request.path_url == path_url
        payload = json.loads(request.body)
        assert payload == expected_payload
        return (200, {}, "")

    responses.add_callback(responses.POST, f"https://api.messagemedia.com{path_url}",
                           callback=request_callback, content_type="application/json")

    mm = MessagesAPI(API_KEY, API_SECRET)
    response = mm.confirm_delivery_reports(["1234-1234-delivery", "1234-5678-delivery"])
    assert response == True     # pylint: disable=singleton-comparison
