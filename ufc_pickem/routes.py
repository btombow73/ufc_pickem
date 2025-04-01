from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required, login_user
from werkzeug.security import generate_password_hash
from .app import db
from .models import User, Fight, Pick, Event
from .forms import RegistrationForm, PickForm
from datetime import datetime
from .extensions import db


main = Blueprint('main', __name__)

@main.route('/')
def index():
    # If logged in, go to dashboard; otherwise, show welcome page
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # Create new user with hashed password
        hashed_pw = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_pw, is_admin=False)
        db.session.add(new_user)
        db.session.commit()
        # Automatically log in the new user after registration
        login_user(new_user)
        flash('Registration successful! You are now logged in.', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('register.html', form=form)

@main.route('/dashboard')
def dashboard():
    # Query all events, order by date (newest first for display)
    events = Event.query.order_by(Event.date.desc()).all()
    upcoming_events = [event for event in events if event.date >= datetime.utcnow().date()]
    past_events = [event for event in events if event.date < datetime.utcnow().date()]
    # Map the current user's picks by fight for quick lookup
    picks_map = {}
    if current_user.is_authenticated:
        user_picks = Pick.query.filter_by(user_id=current_user.id).all()
        picks_map = {pick.fight_id: pick for pick in user_picks}
    return render_template('dashboard.html', upcoming_events=upcoming_events, past_events=past_events, picks_map=picks_map)

@main.route('/picks/<int:fight_id>', methods=['GET', 'POST'])
@login_required
def picks(fight_id):
    fight = Fight.query.get_or_404(fight_id)
    # Prevent picking if fight already has a recorded result
    if fight.winner:
        flash('This fight already has a result; picks are closed.', 'warning')
        return redirect(url_for('main.dashboard'))
    form = PickForm()
    # Dynamically set fighter choices based on this fight
    form.selected_fighter.choices = [
        (fight.fighter1, fight.fighter1),
        (fight.fighter2, fight.fighter2)
    ]
    if request.method == 'GET':
        # If user already made a pick for this fight, pre-fill form for editing
        existing_pick = Pick.query.filter_by(user_id=current_user.id, fight_id=fight.id).first()
        if existing_pick:
            form.selected_fighter.data = existing_pick.selected_fighter
            form.selected_method.data = existing_pick.selected_method
    if form.validate_on_submit():
        pick = Pick.query.filter_by(user_id=current_user.id, fight_id=fight.id).first()
        if pick:
            # Update existing pick
            pick.selected_fighter = form.selected_fighter.data
            pick.selected_method = form.selected_method.data
        else:
            # Create a new pick
            pick = Pick(user_id=current_user.id, fight_id=fight.id,
                        selected_fighter=form.selected_fighter.data,
                        selected_method=form.selected_method.data)
            db.session.add(pick)
        db.session.commit()
        flash('Your pick has been saved!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('picks.html', fight=fight, form=form)

@main.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    # Users can only view their own profile, unless current user is admin
    if user.id != current_user.id and not current_user.is_admin:
        flash('You are not authorized to view this profile.', 'danger')
        return redirect(url_for('main.dashboard'))
    picks = Pick.query.filter_by(user_id=user.id).all()
    # Annotate picks with correctness and score for display
    for pick in picks:
        if pick.fight.winner is None:
            pick.is_correct = None
            pick.score = None
        else:
            pick.is_correct = (pick.selected_fighter == pick.fight.winner)
            # Use the stored points_awarded as the score
            pick.score = pick.points_awarded if pick.points_awarded is not None else 0
    return render_template('profile.html', user=user, picks=picks)

@main.route('/leaderboard')
def leaderboard():
    # Calculate total points for each user (overall leaderboard)
    users = User.query.all()
    for u in users:
        u.points = sum(p.points_awarded for p in u.picks)
    # Sort users by total points (highest first)
    users.sort(key=lambda user: user.points, reverse=True)
    # Determine top performer for each event
    event_winners = []
    events = Event.query.all()
    for event in events:
        user_scores = {}
        for fight in event.fights:
            for pick in fight.picks:
                # Sum points for each user in this event
                user_scores[pick.user_id] = user_scores.get(pick.user_id, 0) + (pick.points_awarded or 0)
        if user_scores:
            top_user_id = max(user_scores, key=user_scores.get)
            top_score = user_scores[top_user_id]
            top_user = User.query.get(top_user_id)
            if top_user:
                event_winners.append({'event': event.name, 'username': top_user.username, 'points': top_score})
    return render_template('leaderboard.html', leaderboard=users, event_winners=event_winners)
