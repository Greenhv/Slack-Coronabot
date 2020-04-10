import os
import re
import logging
import requests

# Slack dependencies
from flask import Flask
from slack import WebClient
from slackeventsapi import SlackEventAdapter

# Env constants
ACCESS_TOKEN = os.environ['SLACK_BOT_ACCESS_TOKEN']
SLACK_SIGNING_SECRET = os.environ['SLACK_BOT_SIGNING_SECRET']
DEFAULT_API_ENDPOINT= os.environ['DEFAULT_API_ENDPOINT']

ENDPOINT_HEADERS = {'User-Agent': 'CoronaBot'}

# Messages
DEFAULT_ERROR_MSG = "Something went wrong, please try again in a bit :pray:"
FORMAT_ERROR_MSG = "I don't understand that :confounded:, to check the format guidelines please send `/help`"
WAIT_FOR_ME_MSG = "Got it... Please wait for me :simple_smile:"

# Patterns
MESSAGE_PATTERN = r'(<@\w*>)?\s*\w*\s*,\s*\w*\s*(,\s*-?\d+)?'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Slack
app = Flask(__name__)
slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, "/api/bot", app)
slack_web_client = WebClient(token=ACCESS_TOKEN)

class FormatException(Exception):
    pass

class RequestException(Exception):
    pass

def send_text(channel_id, message):
    slack_message = {
        "channel": channel_id,
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

    slack_web_client.chat_postMessage(**slack_message)

def send_photo(channel_id, photo_url):
    slack_message = {
        "channel": channel_id,
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
    commandArr = arr[0].strip().split(' ')

    if (len(commandArr) == 1):
        return commandArr[0]
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
        raise FormatException('Incorrect pattern')

    return {
        "command": get_command(message),
        "country": get_country(message),
        "days": get_days(message)
    }

def get_photo_url(command, country, days):
    # send the parameters according to the api
    # photo_url = requests.get(DEFAULT_API_ENDPOINT, headers=ENDPOINT_HEADERS)

    return "https://api.slack.com/img/blocks/bkb_template_images/goldengate.png"

def process_message(channel_id, message):
    try:
        obj_message = parse_message(message)

        send_text(channel_id, WAIT_FOR_ME_MSG)

        photo_url = get_photo_url(**obj_message)
        send_photo(channel_id, photo_url)
    except FormatException as error:
        logger.warning(error)
        send_text(channel_id, FORMAT_ERROR_MSG)
    except Exception as error:
        logger.warning(error)
        send_text(channel_id, DEFAULT_ERROR_MSG)

def message_handler(payload):
    event = payload.get("event", {})
    channel_id = event.get("channel")
    message = event.get("text")
    bot_id = event.get("bot_id")

    if bot_id is None:
        process_message(channel_id, message)

def start_listening():
    slack_events_adapter.on("message", message_handler)
    slack_events_adapter.on("app_mention", message_handler)

if __name__ == 'api.bot':
    start_listening()
