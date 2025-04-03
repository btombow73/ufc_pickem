from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from .models import User, Event

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered.')

class LoginForm(FlaskForm):
    email = StringField('Email or Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class PickForm(FlaskForm):
    selected_fighter = SelectField('Select Fighter', choices=[], validators=[DataRequired()])
    selected_method = SelectField('Select Method of Victory', choices=[
        ('', 'Choose Method'),
        ('KO/TKO', 'KO/TKO'),
        ('Submission', 'Submission'),
        ('Decision', 'Decision')
    ], validators=[DataRequired()])
    selected_round = SelectField('Select Round', choices=[
        ('1', 'Round 1'),
        ('2', 'Round 2'),
        ('3', 'Round 3'),
        ('4', 'Round 4'),
        ('5', 'Round 5'),
        ('Decision', 'Decision')
    ], validators=[DataRequired()])
    submit = SubmitField('Submit Pick')

class FightForm(FlaskForm):
    fighter1 = StringField('Fighter 1', validators=[DataRequired()])
    fighter2 = StringField('Fighter 2', validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])

    favorite = SelectField('Favorite Fighter', choices=[
        ('fighter1', 'Fighter 1'),
        ('fighter2', 'Fighter 2')
    ], validators=[DataRequired()])

    best_method = SelectField('Best Method (Oddsmaker)', choices=[
        ('KO/TKO', 'KO/TKO'),
        ('Submission', 'Submission'),
        ('Decision', 'Decision')
    ], validators=[DataRequired()])

    best_round = SelectField('Best Round (Oddsmaker)', choices=[
        ('1', 'Round 1'),
        ('2', 'Round 2'),
        ('3', 'Round 3'),
        ('4', 'Round 4'),
        ('5', 'Round 5'),
        ('Decision', 'Decision')
    ], validators=[DataRequired()])

    event_id = SelectField('Event', coerce=int, choices=[], validators=[DataRequired()])
    submit = SubmitField('Save Fight')


class FightResultForm(FlaskForm):
    winner = SelectField('Winner', choices=[], validators=[DataRequired()])
    method = SelectField('Method of Victory', choices=[
        ('KO/TKO', 'KO/TKO'),
        ('Submission', 'Submission'),
        ('Decision', 'Decision')
    ], validators=[DataRequired()])
    round = SelectField('Round of Victory', choices=[
        ('1', 'Round 1'),
        ('2', 'Round 2'),
        ('3', 'Round 3'),
        ('4', 'Round 4'),
        ('5', 'Round 5'),
        ('Decision', 'Decision')
    ], validators=[DataRequired()])

    # 🔥 Add these for admin odds
    best_method = SelectField('Best Odds Method', choices=[
        ('KO/TKO', 'KO/TKO'),
        ('Submission', 'Submission'),
        ('Decision', 'Decision')
    ], validators=[DataRequired()])
    
    best_round = SelectField('Best Odds Round', choices=[
        ('1', 'Round 1'),
        ('2', 'Round 2'),
        ('3', 'Round 3'),
        ('4', 'Round 4'),
        ('5', 'Round 5'),
        ('Decision', 'Decision')
    ], validators=[DataRequired()])

    submit = SubmitField('Submit Result')


class DeleteFightForm(FlaskForm):
    confirm = BooleanField('Are you sure you want to delete this fight?', validators=[DataRequired()])
    submit = SubmitField('Delete Fight')

class EventForm(FlaskForm):
    name = StringField('Event Name', validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Create Event')

    def validate_name(self, name):
        event = Event.query.filter_by(name=name.data).first()
        if event:
            raise ValidationError('An event with that name already exists.')
