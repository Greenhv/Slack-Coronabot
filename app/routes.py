import os
import binascii
from urllib.parse import urljoin, urlencode

# Slack dependencies
from flask import Response, session, redirect, request
from slack import WebClient

# App imports
from app import flask_app, db, logger
from .models import SlackWorkspace

# Slack Handlers
from .commands.slash_info import get_help

# Env constants
SLACK_APP_ID = os.environ['SLACK_APP_ID']
SLACK_CLIENT_SECRET = os.environ['SLACK_CLIENT_SECRET']
SLACK_CLIENT_ID = os.environ['SLACK_CLIENT_ID']
SLACK_BASE_URL = os.environ.get('SLACK_BASE_URL') or 'https://slack.com'


def redirect_to_app_page():
    return redirect(urljoin(SLACK_BASE_URL, 'apps/{}'.format(SLACK_APP_ID)))


"""Slack Oauth"""
@flask_app.route('/oauth/login', methods=['GET'])
def login():
    slack_base_url = 'https://slack.com'
    state = binascii.b2a_hex(os.urandom(15))
    session['state'] = state
    qs = {
        'client_id': SLACK_CLIENT_ID,
        'scope': 'app_mentions:read,chat:write,commands,im:history',
        'state': state,
    }
    url_path = '/oauth/v2/authorize?{}'.format(urlencode(qs))

    return redirect(urljoin(slack_base_url, url_path))


@flask_app.route('/oauth/callback', methods=['GET'])
def callback():
    error = request.args.get('error')
    req_state = request.args.get('state')
    req_code = request.args.get('code')
    session_state = session['state']
    logger.info('Callback error {}'.format(error))
    logger.info('Session state {}'.format(session_state))

    if (error and error == 'access_denied'):
        logger.warning('The user aborted OAuth')
        return redirect_to_app_page()

    if req_state is None:
        logger.warning('No state in the request')
        return redirect_to_app_page()

    if session_state is None:
        logger.warning('No state in the sesssion')
        return redirect_to_app_page()

    state_matches = session_state.decode() == req_state

    if not state_matches:
        logger.warning('The request state does not match the session state')
        return redirect_to_app_page()

    logger.info(
        'Getting the access token with the temp code {}'.format(req_code))

    client = WebClient('')
    access = None

    try:
        access = client.oauth_v2_access(
            client_id=SLACK_CLIENT_ID, client_secret=SLACK_CLIENT_SECRET, code=req_code)
    except Exception as error:
        logger.warning('Failed to exchange code for access token')
        logger.warning('Error {}'.format(error))
        return redirect_to_app_page()

    # todo change logger result to app_id
    logger.info('Access response obtained to the workspace {}'.format(
        access.get('team').get('id')))

    team_id = access.get('team').get('id')
    access_token = access.get('access_token')
    workspace = SlackWorkspace.query.filter_by(slack_id=team_id).first()

    if workspace is None:
        workspace = SlackWorkspace(slack_id=team_id, access_token=access_token)
        db.session.add(workspace)
        db.session.commit()
    else:
        workspace.access_token = access_token
        db.session.commit()

    logger.info('Workspace info saved to database')

    qs = {
        'app': access.get('app_id'),
        'team': team_id
    }
    open_app_path = '/app_redirect?{}'.format(urlencode(qs))

    return redirect(urljoin(SLACK_BASE_URL, open_app_path))


"""Slash commands handle by Flask"""
@flask_app.route('/api/info_command', methods=['POST'])
def send_help():
    message = get_help()

    logger.info('sendding help info to the workspace')

    return Response(message)
