from enum import unique
from os import path
from sqlalchemy.sql import func
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

DB_NAME = "daydream_development.db"
DB_LOCATION = "data/database/"

db = SQLAlchemy()


# Database Creation Check
def create_database(app):
    '''Checks if DB exists, else creates new DB'''
    if not path.exists(DB_LOCATION + DB_NAME):
        db.create_all(app=app)


class User(db.Model, UserMixin):
    '''Data model for user table'''
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(42), unique=True)
    sessionid = db.Column(db.String(42), unique=True)
    email = db.Column(db.String(128), unique=True)
    mobile = db.Column(db.String(12))
    password = db.Column(db.String(64))
    tokens = db.Column(db.Integer, default="25")
    username = db.Column(db.String(32))
    first_name = db.Column(db.String(32))
    last_name = db.Column(db.String(32))
    role = db.Column(db.String(32), default="prepaid")
    state = db.Column(db.Boolean, default=True)
    subscription = db.Column(db.Integer)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    jobs = db.relationship('Task')


class Task(db.Model):
    '''Data model for user task'''
    __tablename__ = "task"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    sessionid = db.Column(db.String(42))
    prompt = db.Column(db.String(512))
    imgw = db.Column(db.Integer)
    imgh = db.Column(db.Integer)
    samples = db.Column(db.Integer)
    steps = db.Column(db.Integer)
    guide = db.Column(db.Float)
    seed = db.Column(db.Integer, default="0")
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    timer = db.Column(db.Integer, default="0")
    state = db.Column(db.String(32), default="initiated")
    images = db.relationship('Image')


class Image(db.Model):
    '''Data model for image'''
    __tablename__ = "image"
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    path = db.Column(db.String)
    uuid = db.Column(db.String)