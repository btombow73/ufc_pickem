from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from .forms import FightForm, FightResultForm, DeleteFightForm, EventForm
from .models import Fight, Pick, Event, User
from .extensions import db
from datetime import datetime, timedelta

admin = Blueprint('admin', __name__)

def is_admin():
    return current_user.is_authenticated and current_user.is_admin

@admin.route('/add_event', methods=['GET', 'POST'])
@login_required
def add_event():
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for('main.dashboard'))
    form = EventForm()
    if form.validate_on_submit():
        new_event = Event(name=form.name.data, date=form.date.data)
        db.session.add(new_event)
        db.session.commit()
        flash("Event created successfully!", "success")
        return redirect(url_for('main.dashboard'))
    return render_template('add_event.html', form=form)

@admin.route('/event/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def update_event(event_id):
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for('main.dashboard'))

    event = Event.query.get_or_404(event_id)
    form = EventForm()

    if request.method == 'GET':
        # Pre-fill form with current values
        form.name.data = event.name
        form.date.data = event.date

    if form.validate_on_submit():
        # Update values from form
        event.name = form.name.data
        event.date = form.date.data
        db.session.commit()
        flash("Event updated successfully!", "success")
        return redirect(url_for('main.dashboard'))

    return render_template('update_event.html', form=form, event=event)


@admin.route('/event/<int:event_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_event(event_id):
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for('main.dashboard'))

    event = Event.query.get_or_404(event_id)
    form = DeleteFightForm()  # We’ll reuse the same confirmation form

    if form.validate_on_submit() and form.confirm.data:
        # Delete all fights and picks associated with this event
        for fight in event.fights:
            Pick.query.filter_by(fight_id=fight.id).delete()
            db.session.delete(fight)
        db.session.delete(event)
        db.session.commit()
        flash("Event and its fights were deleted successfully.", "success")
        return redirect(url_for('main.dashboard'))

    return render_template('delete_event.html', event=event, form=form)


@admin.route('/add_fight', methods=['GET', 'POST'])
@login_required
def add_fight():
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for('main.dashboard'))
    events = Event.query.order_by(Event.date).all()
    if not events:
        flash("No events available. Create an event first.", "warning")
        return redirect(url_for('admin.add_event'))
    
    form = FightForm()
    form.event_id.choices = [(event.id, event.name) for event in events]
    
    if form.validate_on_submit():
        favorite_name = form.fighter1.data if form.favorite.data == 'fighter1' else form.fighter2.data
        event = Event.query.get(form.event_id.data)
        new_fight = Fight(
            fighter1=form.fighter1.data,
            fighter2=form.fighter2.data,
            date=form.date.data,
            favorite=favorite_name,
            event=event,
            best_method=form.best_method.data,
            best_round=form.best_round.data
        )
        db.session.add(new_fight)
        db.session.commit()
        flash("Fight added successfully!", "success")
        return redirect(url_for('main.dashboard'))
    
    return render_template('add_fight.html', form=form)


@admin.route('/fight/<int:fight_id>/update', methods=['GET', 'POST'])
@login_required
def update_fight(fight_id):
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for('main.dashboard'))
    
    fight = Fight.query.get_or_404(fight_id)
    events = Event.query.order_by(Event.date).all()
    form = FightForm()
    form.event_id.choices = [(event.id, event.name) for event in events]
    
    if request.method == 'GET':
        form.fighter1.data = fight.fighter1
        form.fighter2.data = fight.fighter2
        form.date.data = fight.date
        form.favorite.data = 'fighter1' if fight.favorite == fight.fighter1 else 'fighter2'
        form.event_id.data = fight.event_id
        form.best_method.data = fight.best_method
        form.best_round.data = fight.best_round
    
    if form.validate_on_submit():
        fight.fighter1 = form.fighter1.data
        fight.fighter2 = form.fighter2.data
        fight.date = form.date.data
        fight.favorite = form.fighter1.data if form.favorite.data == 'fighter1' else form.fighter2.data
        fight.event_id = form.event_id.data
        fight.best_method = form.best_method.data
        fight.best_round = form.best_round.data

        db.session.commit()
        flash("Fight updated successfully!", "success")
        return redirect(url_for('main.dashboard'))
    
    return render_template('update_fight.html', form=form, fight=fight)


@admin.route('/fight/<int:fight_id>/result', methods=['GET', 'POST'])
@login_required
def fight_result(fight_id):
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for('main.dashboard'))

    fight = Fight.query.get_or_404(fight_id)
    form = FightResultForm()
    form.winner.choices = [(fight.fighter1, fight.fighter1), (fight.fighter2, fight.fighter2)]

    if request.method == 'GET' and fight.winner:
        form.winner.data = fight.winner
        form.method.data = fight.method
        form.round.data = fight.round
        form.best_method.data = fight.best_method
        form.best_round.data = fight.best_round

    if form.validate_on_submit():
        fight.winner = form.winner.data
        fight.method = form.method.data
        fight.round = form.round.data
        fight.best_method = form.best_method.data
        fight.best_round = form.best_round.data
        db.session.commit()

        # Score all user picks
        picks = Pick.query.filter_by(fight_id=fight.id).all()
        for pick in picks:
            points = 0
            if pick.selected_fighter == fight.winner:
                points += 1
                if fight.method and pick.selected_method == fight.method:
                    points += 1
                if fight.round and pick.selected_round == fight.round:
                    points += 1
                if fight.winner != fight.favorite:
                    points *= 2
            pick.points_awarded = points

        # Book user logic
        book_user = User.query.filter_by(username='Book').first()
        if not book_user:
            book_user = User(username='Book', email='book@example.com', password='book', is_admin=False)
            db.session.add(book_user)
            db.session.commit()

        book_pick = Pick.query.filter_by(user_id=book_user.id, fight_id=fight.id).first()
        if not book_pick:
            book_pick = Pick(
                user_id=book_user.id,
                fight_id=fight.id,
                selected_fighter=fight.favorite,
                selected_method=fight.best_method,
                selected_round=fight.best_round
            )
            db.session.add(book_pick)
        else:
            book_pick.selected_fighter = fight.favorite
            book_pick.selected_method = fight.best_method
            book_pick.selected_round = fight.best_round

        # Score the book pick
        book_points = 0
        if book_pick.selected_fighter == fight.winner:
            book_points += 1
            if fight.method and book_pick.selected_method == fight.method:
                book_points += 1
            if fight.round and book_pick.selected_round == fight.round:
                book_points += 1
            if fight.winner != fight.favorite:
                book_points *= 2
        book_pick.points_awarded = book_points

        db.session.commit()
        flash("Fight result recorded and Book user updated!", "success")
        return redirect(url_for('main.dashboard'))

    return render_template('fight_result.html', fight=fight, form=form)

@admin.route('/fight/<int:fight_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_fight(fight_id):
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for('main.dashboard'))
    fight = Fight.query.get_or_404(fight_id)
    form = DeleteFightForm()
    if form.validate_on_submit() and form.confirm.data:
        Pick.query.filter_by(fight_id=fight.id).delete()
        db.session.delete(fight)
        db.session.commit()
        flash("Fight deleted successfully.", 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('delete_fight.html', fight=fight, form=form)
@admin.route('/cleanup_unverified')
@login_required
def cleanup_unverified():
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for('main.dashboard'))

    cutoff_date = datetime.utcnow() - timedelta(days=3)
    unverified_users = User.query.filter(
        User.is_verified == False,
        User.created_at < cutoff_date
    ).all()

    count = len(unverified_users)
    for user in unverified_users:
        db.session.delete(user)

    db.session.commit()
    flash(f"Deleted {count} unverified user(s) older than 3 days.", "info")
    return redirect(url_for('main.dashboard'))