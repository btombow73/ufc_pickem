from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField, DateField, RadioField, IntegerField
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
    selected_fighter = RadioField('Fighter', validators=[DataRequired()], choices=[])
    
    selected_method = RadioField('Method of Victory', validators=[DataRequired()], choices=[
        ('KO/TKO', 'KO/TKO'),
        ('Submission', 'Submission'),
        ('Decision', 'Decision')
    ])
    
    selected_round = RadioField('Round of Victory', validators=[DataRequired()], choices=[
        ('1', 'Round 1'),
        ('2', 'Round 2'),
        ('3', 'Round 3'),
        ('4', 'Round 4'),
        ('5', 'Round 5'),
        ('Decision', 'Decision')
    ])
    
    submit = SubmitField('Submit Pick')

class FightForm(FlaskForm):
    fighter1 = StringField('Fighter 1', validators=[DataRequired()])
    fighter2 = StringField('Fighter 2', validators=[DataRequired()])
    fight_rounds = RadioField("Number of Rounds", choices=[ ('3', '3 Rounds'), ('5', '5 Rounds') ], validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    order = IntegerField('Order')  
    favorite = RadioField('Favorite Fighter', choices=[
        ('fighter1', 'Fighter 1'),
        ('fighter2', 'Fighter 2')
    ], validators=[DataRequired()])
    best_method = RadioField('Book Method', choices=[
        ('KO/TKO', 'KO/TKO'),
        ('Submission', 'Submission'),
        ('Decision', 'Decision')
    ], default='Decision')
    best_round = RadioField('Book Round', choices=[
        ('1', 'Round 1'), 
        ('2', 'Round 2'), 
        ('3', 'Round 3'), 
        ('4', 'Round 4'), 
        ('5', 'Round 5'),
        ('Decision', 'Decision')
    ], default='Decision')
    event_id = SelectField('Event', coerce=int, choices=[], validators=[DataRequired()])
    submit = SubmitField('Save Fight')

    def validate(self, extra_validators=None):
        if not super().validate():
            return False

        if self.best_method.data == 'Decision' and self.best_round.data != 'Decision':
            self.best_round.errors.append("Round must be 'Decision' when method is 'Decision'.")
            return False

        if self.best_method.data != 'Decision' and self.best_round.data == 'Decision':
            self.best_round.errors.append("'Decision' round is only valid if the method is 'Decision'.")
            return False

        return super().validate(extra_validators=extra_validators)


class FightResultForm(FlaskForm):
    winner = RadioField('Winner', choices=[], validators=[DataRequired()])
    method = RadioField('Method of Victory', choices=[
        ('KO/TKO', 'KO/TKO'),
        ('Submission', 'Submission'),
        ('Decision', 'Decision')
    ], validators=[DataRequired()])
    round = RadioField('Round of Victory', choices=[
        ('1', 'Round 1'),
        ('2', 'Round 2'),
        ('3', 'Round 3'),
        ('4', 'Round 4'),
        ('5', 'Round 5'),
        ('Decision', 'Decision')
    ], validators=[DataRequired()])

    best_method = RadioField('Best Odds Method', choices=[
        ('KO/TKO', 'KO/TKO'),
        ('Submission', 'Submission'),
        ('Decision', 'Decision')
    ], validators=[DataRequired()])
    
    best_round = RadioField('Best Odds Round', choices=[
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
    submit = SubmitField('Create Event')
    
    def validate_name(self, name):
        event = Event.query.filter_by(name=name.data).first()
        if event:
            raise ValidationError('An event with that name already exists.')
