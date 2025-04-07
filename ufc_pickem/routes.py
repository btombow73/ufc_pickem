from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required, login_user
from werkzeug.security import generate_password_hash
from .models import User, Fight, Pick, Event
from .forms import RegistrationForm, PickForm
from .extensions import db
from .mailgun_utils import send_verification_email
from datetime import datetime
import secrets
from zoneinfo import ZoneInfo


main = Blueprint('main', __name__)


@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')


@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)
        token = secrets.token_urlsafe(32)

        new_user = User(
            username=form.username.data.lower(),
            email=form.email.data.lower(),
            password=hashed_pw,
            is_admin=False,
            is_verified=False,
            verification_token=token
        )

        db.session.add(new_user)
        db.session.commit()

        send_verification_email(new_user.email, token)

        flash('Account created! Please check your email to verify your account.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)


@main.route('/verify/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if user:
        user.is_verified = True
        user.verification_token = None
        db.session.commit()
        flash("Email verified! You can now use your account.", "success")
    else:
        flash("Invalid or expired verification link.", "danger")
    return redirect(url_for('main.dashboard'))

@main.route('/resend-verification')
@login_required
def resend_verification():
    if current_user.is_verified:
        flash("Your email is already verified.", "info")
        return redirect(url_for('main.dashboard'))

    # Regenerate token
    token = secrets.token_urlsafe(32)
    current_user.verification_token = token
    db.session.commit()

    send_verification_email(current_user.email, token)
    flash("Verification email sent. Please check your inbox.", "success")
    return redirect(url_for('main.dashboard'))


@main.route('/dashboard')
def dashboard():
    events = Event.query.order_by(Event.date.desc()).all()
    upcoming_events = [event for event in events if event.date >= datetime.utcnow().date()]
    past_events = [event for event in events if event.date < datetime.utcnow().date()]

    # Sort fights by order with fallback to 9999 for None
    for event in events:
        event.fights = sorted(event.fights, key=lambda f: f.order if f.order is not None else 9999)

    picks_map = {}
    if current_user.is_authenticated:
        user_picks = Pick.query.filter_by(user_id=current_user.id).all()
        picks_map = {pick.fight_id: pick for pick in user_picks}

    return render_template('dashboard.html', upcoming_events=upcoming_events, past_events=past_events, picks_map=picks_map)



@main.route('/picks/<int:fight_id>', methods=['GET', 'POST'])
@login_required
def picks(fight_id):
    if not current_user.is_verified:
        flash("Please verify your email to make picks.", "warning")
        return redirect(url_for('main.dashboard'))

    fight = Fight.query.get_or_404(fight_id)
    if fight.winner:
        flash('This fight already has a result; picks are closed.', 'warning')
        return redirect(url_for('main.dashboard'))

    form = PickForm()
    # Dynamically set the available rounds based on admin selection
    form.selected_round.choices = [(str(i), f"Round {i}") for i in range(1, fight.fight_rounds + 1)]
    if 'Decision' not in [r[0] for r in form.selected_round.choices]:
        form.selected_round.choices.append(('Decision', 'Decision'))


    form.selected_fighter.choices = [
        (fight.fighter1, fight.fighter1),
        (fight.fighter2, fight.fighter2)
    ]

    if request.method == 'GET':
        existing_pick = Pick.query.filter_by(user_id=current_user.id, fight_id=fight.id).first()
        if existing_pick:
            form.selected_fighter.data = existing_pick.selected_fighter
            form.selected_method.data = existing_pick.selected_method
            form.selected_round.data = existing_pick.selected_round

    if form.validate_on_submit():
        pick = Pick.query.filter_by(user_id=current_user.id, fight_id=fight.id).first()
        if pick:
            pick.selected_fighter = form.selected_fighter.data
            pick.selected_method = form.selected_method.data
            pick.selected_round = form.selected_round.data
        else:
            pick = Pick(
                user_id=current_user.id,
                fight_id=fight.id,
                selected_fighter=form.selected_fighter.data,
                selected_method=form.selected_method.data,
                selected_round=form.selected_round.data
            )
            db.session.add(pick)

        db.session.commit()
        flash('Your pick has been saved!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('picks.html', fight=fight, form=form)


@main.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    if not current_user.is_verified:
        flash("Please verify your email to view profiles.", "warning")
        return redirect(url_for('main.dashboard'))

    user = User.query.get_or_404(user_id)
    if user.id != current_user.id and not current_user.is_admin:
        flash('You are not authorized to view this profile.', 'danger')
        return redirect(url_for('main.dashboard'))

    picks = Pick.query.filter_by(user_id=user.id).all()
    for pick in picks:
        if pick.fight.winner is None:
            pick.is_correct = None
            pick.score = None
        else:
            pick.is_correct = (pick.selected_fighter == pick.fight.winner)
            pick.score = pick.points_awarded if pick.points_awarded is not None else 0

    return render_template('profile.html', user=user, picks=picks)


@main.route('/leaderboard')
@login_required
def leaderboard():
    if not current_user.is_verified:
        flash("Please verify your email to view the leaderboard.", "warning")
        return redirect(url_for('main.dashboard'))

    users = User.query.all()
    for user in users:
        user.points = sum(p.points_awarded for p in user.picks)

    users.sort(key=lambda u: u.points, reverse=True)

    event_winners = []
    events = Event.query.all()
    for event in events:
        user_scores = {}
        for fight in event.fights:
            for pick in fight.picks:
                user_scores[pick.user_id] = user_scores.get(pick.user_id, 0) + (pick.points_awarded or 0)
        if user_scores:
            top_user_id = max(user_scores, key=user_scores.get)
            top_user = User.query.get(top_user_id)
            if top_user:
                event_winners.append({
                    'event': event.name,
                    'username': top_user.username,
                    'points': user_scores[top_user_id]
                })

    return render_template('leaderboard.html', leaderboard=users, event_winners=event_winners)
