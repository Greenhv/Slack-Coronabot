# App imports
from app import flask_app, logger

def start_listening():
    logger.info('Start listening for slacks events')
    flask_app.run(port=3000)

if __name__ == '__main__':
    start_listening()
