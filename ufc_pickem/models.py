from flask_login import UserMixin
from datetime import datetime
from .app import db
from .extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Relationship: one user to many picks
    picks = db.relationship('Pick', back_populates='user', cascade='all, delete-orphan')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    date = db.Column(db.Date, nullable=False)
    # Relationship: one event to many fights
    fights = db.relationship('Fight', back_populates='event', cascade='all, delete-orphan')

    def __repr__(self):
        return f"Event('{self.name}', date={self.date})"

class Fight(db.Model):
    __tablename__ = 'fight'
    id = db.Column(db.Integer, primary_key=True)
    fighter1 = db.Column(db.String(100), nullable=False)
    fighter2 = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    winner = db.Column(db.String(100), nullable=True)       # After fight, who won
    method = db.Column(db.String(100), nullable=True)       # Method of victory
    favorite = db.Column(db.String(100), nullable=False)    # Name of the favorite fighter
    # Relationship: one fight to many picks
    picks = db.relationship('Pick', back_populates='fight', cascade='all, delete-orphan')
    # Relationship: fight belongs to one event
    event = db.relationship('Event', back_populates='fights')

    def __repr__(self):
        return f"Fight('{self.fighter1} vs {self.fighter2}', date={self.date})"

class Pick(db.Model):
    __tablename__ = 'pick'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fight_id = db.Column(db.Integer, db.ForeignKey('fight.id'), nullable=False)
    selected_fighter = db.Column(db.String(100), nullable=False)
    selected_method = db.Column(db.String(100), nullable=True)
    points_awarded = db.Column(db.Integer, default=0)
    # Relationships back to user and fight
    user = db.relationship('User', back_populates='picks')
    fight = db.relationship('Fight', back_populates='picks')

    def __repr__(self):
        return f"Pick(User={self.user_id}, Fight={self.fight_id}, Picked='{self.selected_fighter}', Points={self.points_awarded})"
