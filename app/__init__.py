import logging
from os import environ

# Flask
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Slack
from slackeventsapi import SlackEventAdapter

# Env constants
SLACK_SIGNING_SECRET = environ['SLACK_BOT_SIGNING_SECRET']
APP_SECRET_KEY = environ['APP_SECRET_KEY']
DB_SECRET_KEY = environ['DB_SECRET_KEY']

# Logger config
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
flask_app = Flask(__name__)
flask_app.config.from_object(Config)
flask_app.secret_key = APP_SECRET_KEY
db = SQLAlchemy(flask_app)
db_secret = DB_SECRET_KEY
migrate = Migrate(flask_app, db)

# Slack
slack_events_adapter = SlackEventAdapter(
    SLACK_SIGNING_SECRET, "/api/bot", flask_app)

from app import routes, models  # noqa
from app.commands.event_message import message_handler  # noqa
