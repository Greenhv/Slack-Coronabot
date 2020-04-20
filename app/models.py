from app import db, db_secret
from sqlalchemy_utils import EncryptedType


class SlackWorkspace(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement="auto")
    slack_id = db.Column(db.String(128),
                         index=True, nullable=False, unique=True)
    access_token = db.Column(EncryptedType(
        db.String(128), db_secret), nullable=False)

    def __repr__(self):
        return '<SlackWorkspace {}>'.format(self.slack_id)
