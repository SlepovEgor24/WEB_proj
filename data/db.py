from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, timedelta

db = SQLAlchemy()


class User(db.Model):  # Модель пользователя системы
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Integer, default=0)
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender',
                                    lazy=True)
    messages_received = db.relationship('Message', foreign_keys='Message.recipient_id',
                                        backref='recipient', lazy=True)


class Message(db.Model):  # Модель сообщения между пользователями
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime,
                          default=lambda: datetime.now(timezone.utc) + timedelta(hours=3))
    is_read = db.Column(db.Boolean, default=False)
    reply_to_id = db.Column(db.Integer, db.ForeignKey('messages.id'))
    replies = db.relationship('Message', backref=db.backref('original_message', remote_side=[id]),
                              lazy=True)


def init_db(app):  # Инициализация базы данных
    db.init_app(app)
    with app.app_context():
        db.create_all()
