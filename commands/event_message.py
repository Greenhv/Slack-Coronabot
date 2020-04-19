import os
import re
import logging
import requests
from urllib.parse import urljoin

# Slack dependencies
from flask import Flask, jsonify, request
from slack import WebClient
from slackeventsapi import SlackEventAdapter

# Env constants
ACCESS_TOKEN = os.environ['SLACK_BOT_ACCESS_TOKEN']
SLACK_SIGNING_SECRET = os.environ['SLACK_BOT_SIGNING_SECRET']
PLOT_API_ENDPOINT = os.environ['PLOT_API_ENDPOINT']


# Messages
FORMAT_ERROR_MSG = "I don't understand that :confounded:, to check the format guidelines please send `/info`"
API_ERROR_MSG = "Something went wrong while plotting :disappointed:, please try again in a moment"
WAIT_FOR_ME_MSG = "Got it... Please wait for me :simple_smile:"
ADDITIONAL_INFO_MSG = " In case you need help please send `/info`"

# Patterns
MESSAGE_PATTERN = r'(<@\w*>)?\s*\w*\s*,\s*\w*\s*(,\s*-?\d+)?'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Slack
app = Flask(__name__)
slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, "/api/bot", app)
slack_web_client = WebClient(token=ACCESS_TOKEN)

event_attributes = {}

class BotException(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message

        if status_code is not None:
            self.status_code = status_code

        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message

        return rv

def create_text_msg(message, with_user = False):
    user_id = event_attributes.get('user') if with_user else None
 
    return {
        "channel": event_attributes.get('channel'),
        "user": user_id,
        "text": message,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            }
        ]
    }

def send_text(message):
    slack_message = create_text_msg(message)
    slack_web_client.chat_postMessage(**slack_message)

def send_private_text(message):
    slack_message = create_text_msg(message, True)
    slack_web_client.chat_postEphemeral(**slack_message)

def send_photo(photo_url):
    slack_message = {
        "channel": event_attributes.get('channel'),
        "blocks": [
            {
                "type": "image",
                "title": {
                    "type": "plain_text",
                    "text": "Plot image",
                    "emoji": True
                },
                "image_url": photo_url,
                "alt_text": "Plot image"
            }
        ]
    }
    slack_web_client.chat_postMessage(**slack_message)

def get_command(msg):
    arr = msg.split(',')
    commandArr = arr[0].strip().split('>')

    if (len(commandArr) == 1):
        return commandArr[0].strip().lower()
    else:
        return commandArr[1].strip().lower()

def get_country(msg):
    arr = msg.split(',')

    return arr[1].strip().lower()

def get_days(msg):
    arr = msg.split(',')
    
    if (len(arr) == 3):
        return arr[2].strip()

def parse_message(message):
    message_match = re.search(MESSAGE_PATTERN, message)

    if not message_match:
        raise BotException('Incorrect pattern', 400, { "chat_message": FORMAT_ERROR_MSG })

    days = get_days(message)

    if not days:
        days = 0

    return {
        "command": get_command(message),
        "country": get_country(message),
        "days": days
    }

def get_photo_url(**params):
    url = urljoin(PLOT_API_ENDPOINT, 'plot')
    response = requests.get(url, params=params)
    response_obj = response.json()
    status_code = response.status_code

    if status_code == requests.codes['server_error']:
        raise BotException('The server failed and returned with the code {}'.format(status_code), 500, { "chat_message": API_ERROR_MSG })
    elif status_code == requests.codes['not_found']:
        raise BotException('Incorrect pattern', 400, { "chat_message":  API_ERROR_MSG })
    elif status_code == requests.codes['unprocessable_entity']:
        error = response.json().get('errors').get('error')
        raise BotException(error, 400, { "chat_message":  error + ADDITIONAL_INFO_MSG })

    return response_obj.get('message')

@app.errorhandler(BotException)
def handle_bot_exception(error):
    error_obj = error.to_dict()
    chat_message = error_obj.get('chat_message')
    event_type = event_attributes.get('type')
    response = jsonify(error_obj)
    response.status_code = error.status_code
    response.headers['X-Slack-No-Retry'] = 1

    logger.warning("Status code: {} - ".format(error.status_code) + error_obj.get("message"))

    if chat_message:
        if event_type == 'message':
            send_text(error_obj.get("chat_message"))
        else:
            send_private_text(error_obj.get("chat_message"))

    return response

def process_message(message):
    obj_message = parse_message(message)
    photo_url = get_photo_url(**obj_message)

    send_text(WAIT_FOR_ME_MSG)
    send_photo(photo_url)

def message_handler(payload):
    global event_attributes

    event = payload.get("event", {})
    sub_type = event.get("subtype")
    message_edited = event.get("edited")
    message = event.get("text")
    bot_id = event.get("bot_id")
    event_attributes = event.copy()
    retry_header = request.headers.get('X-Slack-Retry-Num')
    is_not_bot_message = bot_id is None
    is_not_retry_message = retry_header is None
    is_not_edited_direct_message = sub_type is None
    is_not_edited_channel_message = message_edited is None

    if is_not_bot_message and is_not_retry_message and is_not_edited_direct_message and is_not_edited_channel_message:
        process_message(message)

