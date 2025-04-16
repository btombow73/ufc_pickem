from flask_login import UserMixin
from datetime import datetime
from .extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), nullable=True)
    reset_token = db.Column(db.String(100), nullable=True)


    # One user to many picks
    picks = db.relationship('Pick', back_populates='user', cascade='all, delete-orphan')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    is_locked = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    # One event to many fights
    fights = db.relationship('Fight', back_populates='event', cascade='all, delete-orphan')

    def __repr__(self):
        return f"Event('{self.name}')"


class Fight(db.Model):
    __tablename__ = 'fight'
    id = db.Column(db.Integer, primary_key=True)
    fighter1 = db.Column(db.String(100), nullable=False)
    fighter2 = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    favorite = db.Column(db.String(100), nullable=False)
    winner = db.Column(db.String(100), nullable=True)
    method = db.Column(db.String(100), nullable=True)
    round = db.Column(db.String(100), nullable=True)
    fight_rounds = db.Column(db.Integer, nullable=False, default=3)
    order = db.Column(db.Integer, default=0)
    best_method = db.Column(db.String(100), nullable=True)
    best_round = db.Column(db.String(100), nullable=True)

    # Relationships
    picks = db.relationship('Pick', back_populates='fight', cascade='all, delete-orphan')
    event = db.relationship('Event', back_populates='fights')

    def __repr__(self):
        return f"Fight('{self.fighter1} vs {self.fighter2}', date={self.date})"

class Fighter(db.Model):
    __tablename__ = 'fighters'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(255))
    weight_class = db.Column(db.String(100))
    record = db.Column(db.String(100))
    knockouts = db.Column(db.String(100))
    submissions = db.Column(db.String(100))
    first_round_finishes = db.Column(db.String(100))
    takedown_accuracy = db.Column(db.String(100))
    striking_accuracy = db.Column(db.String(100))
    sig_str_landed_total = db.Column(db.String(100))
    sig_str_attempted_total = db.Column(db.String(100))
    takedowns_landed_total = db.Column(db.String(100))
    takedowns_attempted_total = db.Column(db.String(100))
    sig_strikes_per_min = db.Column(db.String(100))
    takedown_avg_per_min = db.Column(db.String(100))
    sig_str_def = db.Column(db.String(100))
    knockdown_avg = db.Column(db.String(100))
    sig_strikes_absorbed_per_min = db.Column(db.String(100))
    sub_avg_per_min = db.Column(db.String(100))
    takedown_def = db.Column(db.String(100))
    avg_fight_time = db.Column(db.String(100))
    sig_strikes_while_standing = db.Column(db.String(100))
    sig_strikes_while_clinched = db.Column(db.String(100))
    sig_strikes_while_grounded = db.Column(db.String(100))
    win_by_ko_tko = db.Column(db.String(100))
    win_by_decision = db.Column(db.String(100))
    win_by_submission = db.Column(db.String(100))
    image_url = db.Column(db.String(500))

    def __repr__(self):
        return f"<Fighter {self.name}>"


class Pick(db.Model):
    __tablename__ = 'pick'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fight_id = db.Column(db.Integer, db.ForeignKey('fight.id'), nullable=False)
    selected_fighter = db.Column(db.String(100), nullable=False)
    selected_method = db.Column(db.String(100), nullable=True)
    selected_round = db.Column(db.String(100), nullable=True)
    points_awarded = db.Column(db.Integer, default=0)

    # Relationships
    user = db.relationship('User', back_populates='picks')
    fight = db.relationship('Fight', back_populates='picks')

    def __repr__(self):
        return f"Pick(User={self.user_id}, Fight={self.fight_id}, Picked='{self.selected_fighter}', Points={self.points_awarded})"
