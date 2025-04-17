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
import pandas as pd
import os
from .utils import evaluate_badges_for_user

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
@login_required
def dashboard():
    events = Event.query.all()
    upcoming_events = [event for event in events if not event.is_archived]
    past_events = [event for event in events if event.is_archived]

    # Sort fights by order with fallback to 9999 for None
    for event in events:
        event.fights = sorted(event.fights, key=lambda f: f.order if f.order is not None else 9999)

    # Get current user's picks
    picks_map = {}
    if current_user.is_authenticated:
        user_picks = Pick.query.filter_by(user_id=current_user.id).all()
        picks_map = {pick.fight_id: pick for pick in user_picks}

    # ✅ Fix: Get Book user's picks, joined with fights
    book_picks_map = {}
    book_user = User.query.filter_by(username="Book").first()
    if book_user:
        book_picks = (
            Pick.query
            .filter_by(user_id=book_user.id)
            .join(Pick.fight)
            .all()
        )
        for pick in book_picks:
            book_picks_map[pick.fight_id] = pick

    return render_template(
        'dashboard.html',
        upcoming_events=upcoming_events,
        past_events=past_events,
        picks_map=picks_map,
        book_picks_map=book_picks_map
    )


@main.route('/picks/<int:fight_id>', methods=['GET', 'POST'])
@login_required
def picks(fight_id):
    if not current_user.is_verified:
        flash("Please verify your email to make picks.", "warning")
        return redirect(url_for('main.dashboard'))

    # Fetch the fight data
    fight = Fight.query.get_or_404(fight_id)
    event = fight.event
    if event.is_locked:
        flash("Picks for this event are locked.", "warning")
        return redirect(url_for('main.dashboard'))

    if fight.winner:
        flash('This fight already has a result; picks are closed.', 'warning')
        return redirect(url_for('main.dashboard'))

    form = PickForm()
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

    return render_template("picks.html", fight=fight, form=form)


@main.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    if not current_user.is_verified:
        flash("Please verify your email to view profiles.", "warning")
        return redirect(url_for('main.dashboard'))

    user = User.query.get_or_404(user_id)
    if user.id != current_user.id and not current_user.is_admin:
        pass  # Let anyone view profiles

    selected_event_id = request.args.get('event_id', type=int)

    all_picks = (
        Pick.query
        .filter_by(user_id=user.id)
        .join(Pick.fight)
        .join(Fight.event)
        .all()
    )

    # Only show picks if the event is locked or the fight result is known
    filtered_picks = []
    for pick in all_picks:
        event = pick.fight.event
        if pick.fight.winner is not None or event.is_locked:
            if pick.fight.winner is None:
                pick.is_correct = None
                pick.score = None
            else:
                pick.is_correct = (pick.selected_fighter == pick.fight.winner)
                pick.score = pick.points_awarded if pick.points_awarded is not None else 0
            filtered_picks.append(pick)

    # Group picks by event
    grouped_picks = {}
    events_by_id = {}

    for pick in filtered_picks:
        event = pick.fight.event
        if selected_event_id and event.id != selected_event_id:
            continue
        if event.id not in grouped_picks:
            grouped_picks[event.id] = []
            events_by_id[event.id] = event
        grouped_picks[event.id].append(pick)

    # Sort events (by ID for now) and fights by order
    grouped_picks = dict(sorted(grouped_picks.items(), key=lambda item: item[0], reverse=True))
    for pick_list in grouped_picks.values():
        pick_list.sort(key=lambda p: p.fight.order if p.fight.order is not None else 9999)

    # For event dropdown filter
    all_events = sorted({p.fight.event for p in filtered_picks}, key=lambda e: e.id, reverse=True)
    events_by_id = {e.id: e for e in all_events}

    return render_template(
        'profile.html',
        user=user,
        grouped_picks=grouped_picks,
        events=all_events,
        selected_event_id=selected_event_id,
        events_by_id=events_by_id
    )

@main.route('/leaderboard')
@login_required
def leaderboard():
    if not current_user.is_verified:
        flash("Please verify your email to view the leaderboard.", "warning")
        return redirect(url_for('main.dashboard'))

    # Fetch all events ordered by most recent
    events = Event.query.order_by(Event.id.desc()).all()
    selected_event_id = request.args.get('event_id', type=int)

    # Default to most recent event if none selected
    if selected_event_id is None and events:
        selected_event_id = events[0].id

    filtered_leaderboard = []
    selected_event = None

    if selected_event_id == 0:  # All-time leaderboard
        users = User.query.all()
        for user in users:
            user.points = sum(p.points_awarded or 0 for p in user.picks)
            user.badges = [
                ub.badge for ub in user.user_badges
                if ub.badge and ub.badge.event_id is None  # all-time only
            ]
            filtered_leaderboard.append(user)
        filtered_leaderboard.sort(key=lambda u: u.points, reverse=True)

    else:  # Specific event
        selected_event = Event.query.get(selected_event_id)
        if selected_event:
            event_scores = {}
            for fight in selected_event.fights:
                for pick in fight.picks:
                    event_scores[pick.user_id] = event_scores.get(pick.user_id, 0) + (pick.points_awarded or 0)
            for user_id, points in event_scores.items():
                user = User.query.get(user_id)
                if user:
                    user.points = points
                    user.badges = [
                        ub.badge for ub in user.user_badges
                        if ub.badge and ub.badge.event_id == selected_event_id
                    ]
                    filtered_leaderboard.append(user)
            filtered_leaderboard.sort(key=lambda u: u.points, reverse=True)

    # Top performer per event
    event_winners = []
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

    return render_template(
        'leaderboard.html',
        leaderboard=filtered_leaderboard,
        events=events,
        selected_event_id=selected_event_id,
        event_winners=event_winners
    )

