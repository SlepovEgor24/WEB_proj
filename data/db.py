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
    show_email = db.Column(db.Boolean, default=True)  # Новое поле: показывать email
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
    rating_change = db.Column(db.Integer, default=0)  # Новое поле: изменение рейтинга (+1, -1, 0)
    rating_changed = db.Column(db.Boolean, default=False)  # Флаг: рейтинг уже изменён
    replies = db.relationship('Message', backref=db.backref('original_message', remote_side=[id]),
                              lazy=True)


class Direction(db.Model):  # Модель направления
    __tablename__ = 'directions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_path = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    laws = db.relationship('Law', backref='direction', lazy=True)


class Law(db.Model):  # Модель закона/формулы
    __tablename__ = 'laws'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    direction_id = db.Column(db.Integer, db.ForeignKey('directions.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    text = db.Column(db.Text, nullable=False)


def init_db(app):  # Инициализация базы данных
    db.init_app(app)
    with app.app_context():
        db.create_all()