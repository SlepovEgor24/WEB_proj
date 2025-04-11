from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Integer, default=0)

    def to_dict(self, only=()):
        if only:
            return {field: getattr(self, field) for field in only}
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()