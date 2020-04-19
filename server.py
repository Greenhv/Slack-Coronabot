import os
import logging
import binascii
from urllib.parse import urljoin, urlencode

# Slack dependencies
from flask import Flask, Response, session, redirect, request
from slackeventsapi import SlackEventAdapter

# Slack Handlers
from commands.event_message import message_handler
from commands.slash_info import get_help

# Env constants
SLACK_SIGNING_SECRET = os.environ['SLACK_BOT_SIGNING_SECRET']
APP_SECRET_KEY = os.environ['APP_SECRET_KEY']
APP_ID = os.environ['APP_ID']
CLIENT_ID = os.environ['SLACK_CLIENT_ID']
SLACK_BASE_URL = os.environ['SLACK_BASE_URL'] or 'https://slack.com'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Slack
app = Flask(__name__)
app.secret_key = APP_SECRET_KEY
slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, "/api/bot", app)

"""Slack Oauth"""
@app.route('/oauth/login', methods=['GET'])
def login():
    slack_base_url = 'https://slack.com'
    state = binascii.b2a_hex(os.urandom(15))
    session['state'] = state
    qs = {
        'client_id': CLIENT_ID,
        'scope': 'app_mentions:read,chat:write,commands,im:history',
        'state': state,
    }
    url_path = '/oauth/v2/authorize?{}'.format(urlencode(qs)) 

    return redirect(urljoin(slack_base_url, url_path))


@app.route('/oauth/callback', methods=['GET'])
def callback():
    error = request.args.get('error')
    logger.info(error)

    if (error and error == 'access_denied'):
        return redirect(urljoin(SLACK_BASE_URL, 'apps/{}'.format(APP_ID)))

"""Slash commands handle by flask"""
@app.route('/api/info_command', methods=['POST'])
def send_help():
    message = get_help()

    logger.info('sendding help info to the workspace')
    return Response(message)

"""Event listeners handle by the Events API"""
def start_listening():
    logger.info('Start listening for slacks events')

    slack_events_adapter.on("message", message_handler)
    slack_events_adapter.on("app_mention", message_handler)
    app.run(port=3000)

if __name__ == '__main__':
    start_listening()
