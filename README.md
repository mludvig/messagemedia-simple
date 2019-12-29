# Simple MessageMedia API wrapper

[![PyPI Version](https://img.shields.io/pypi/v/messagemedia-simple.svg?color=4fc921)](https://pypi.org/project/messagemedia-simple/)
[![CircleCI](https://circleci.com/gh/mludvig/messagemedia-simple.svg?style=shield)](https://circleci.com/gh/mludvig/messagemedia-simple)
[![Python Versions](https://img.shields.io/pypi/pyversions/messagemedia-simple.svg)](https://pypi.org/project/messagemedia-simple/)

Simple and easy to use module for sending SMS and MMS messages through [MessageMedia API](https://developers.messagemedia.com/code/messages-api-documentation/).

## Installation

The easiest way is to install the package from [Python Package Index](https://pypi.org/project/messagemedia-simple/):

```
pip3 install messagemedia-simple
```

Note that `messagemedia-simple` is *only available* for **Python 3.6 and newer**. Installation for older Python versions will fail.

## Usage - sending a SMS message

The module interface pretty much mirrors the [MessageMedia *Mesages* API](https://developers.messagemedia.com/code/messages-api-documentation/).
Refer to the API documentation for details about all the possible settings.

```
from messagemedia_simple import MessagesAPI

API_KEY = "ABCDEFGH1234567890XX"
API_SECRET = "1234567890asdfghjkl1234567890x"

# MessageMedia API object
mm = MessagesAPI(API_KEY, API_SECRET, hmac_auth=True)

# Send a SMS message and print `message_id`
send_response = mm.send_message("Some content", "+1234567890")
print(f"message_id: {send_response['message_id']})
```

Now we can check the message delivery status as it progresses from *enroute* through *submitted* to *delivered*:

```
status_response = mm.get_message_status(send_response["message_id"])
print(f"status: {status_response['status']})
```

And finally we can retrieve *Message Replies*. Unfortunately through the API we can only
retrieve *all* queued, unconfirmed replies rather than just those for a given `message_id`.
The filtering has to be done locally after all the replies are retrieved.

```
# Retrieve all replies from MessageMedia
replies_response = mm.get_replies()

# Filter only the relevant replies
my_replies = [r for r in replies_response["replies"] if r["message_id"]==send_response["message_id"]]

# Process the replies
for reply in my_replies:
  print(f"{reply['content']}")
```

MessageMedia API has a concept of *confirming a reply* - as soon as a reply is confirmed it is no longer
returned from `get_replies()` call. That means only confirm a reply after it's successfully processed,
for example written to a local database. Multiple replies can be confirmed at once if needed.

```
for reply in my_replies:
  print(f"{reply['content']}")
  mm.confirm_replies(reply["reply_id"])
```

Likewise we can retrieve and confirm the delivery reports using `get_delivery_reports()` and
`confirm_delivery_reports()`. The logic of the operation is the same as with replies.

## Author

Michael Ludvig <mludvig@logix.net.nz>
