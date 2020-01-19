from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    tier = db.Column(db.String(120))
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Animal(db.Model):
    name = db.Column(db.String(80), unique=True, nullable=False, primary_key=True)
    typ = db.Column(db.String(150))
    intake = db.Column(db.Float, default=2)

    def __repr__(self):
        return "<Animal: {}>".format(self.name)


class Feeder(db.Model):
    number = db.Column(db.Integer, unique=True, nullable=False, primary_key=True)
    wifi = db.Column(db.String(150))
    activation = db.Column(db.String(150))
    # The relationship is established here as well to allow deletion of one feeder and all of its dates.
    date = db.relationship("Date", back_populates='feeder',cascade="all, delete, delete-orphan")

    def __repr__(self):
        return '<Feeder %r>' % self.number

    @staticmethod
    def as_dict():
        feeders = Feeder.query.all()
        return {c.number: {
            "wifi": c.wifi,
            "activation": c.activation,
            "schedule": [d.date for d in c.dates]
            } for c in feeders}


class Date(db.Model):
    date = db.Column(db.DateTime, nullable=False, primary_key=True)
    feeder_id = db.Column(db.Integer, db.ForeignKey('feeder.number'),nullable=False)
    feeder = db.relationship('Feeder', backref=db.backref('dates', lazy=True),single_parent=True)

    def __repr__(self):
        return '<Date %r>' % self.date

'''
Example of Use

from app.tables import Feeder,Date
from datetime import datetime
py = Feeder(number=1,wifi="Connected",activation="Activated")
Date(date=datetime(1, 1, 1, 0, 0, 0),feeder=py)
py.dates

'''