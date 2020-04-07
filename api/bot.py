import os
import re
import logging
import requests

# Slack dependencies
from flask import Flask
from slack import WebClient
from slackeventsapi import SlackEventAdapter

ACCESS_TOKEN = os.environ['SLACK_BOT_ACCESS_TOKEN']
SLACK_SIGNING_SECRET = os.environ['SLACK_BOT_SIGNING_SECRET']
DEFAULT_API_ENDPOINT= os.environ['DEFAULT_API_ENDPOINT']
ENDPOINT_HEADERS = {'User-Agent': 'CoronaBot'}
DEFAULT_ERROR_MSG = 'Something went wrong, please try again in a bit'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Slack
app = Flask('Slack Coronabot')
slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, "/slack/events", app)
slack_web_client = WebClient(token=ACCESS_TOKEN)

def send_text(channel_id, message):
    slack_message = {
        "channel": channel_id,
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
                    "text": "Example Image",
                    "emoji": True
                },
                "image_url": photo_url,
                "alt_text": ""
            }
        ]
    }
    slack_web_client.chat_postMessage(**slack_message)

def parse_message(message):
    arr = message.split(',')

    return {
        "command": arr[0],
        "country": arr[1],
        "days": arr[2]
    }

def get_photo_url(command, country, days):
    # send the parameters according to the api
    photo_url = requests.get(DEFAULT_API_ENDPOINT, headers=ENDPOINT_HEADERS)

    return photo_url

def send_plot(channel_id, message):
    try:
        obj_message = parse_message(message)
        photo_url = get_photo_url(**obj_message)
        send_photo(channel_id, photo_url)
    except Exception as error:
        logger.warning(error)
        send_text(channel_id, DEFAULT_ERROR_MSG)

def send_message(payload):
    event = payload.get("event", {})
    channel_id = event.get("channel")
    message = event.get("text")

    send_plot(channel_id, message)

def start_listening():
    slack_events_adapter.on("message", send_message)
    slack_events_adapter.on("app_mention", send_message)

    logger.info("Start listening for Slack events")

    # flask_app.run(port=4000)

def main():
    start_listening()

if __name__ == '__main__':
    main()
