from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from .forms import FightForm, FightResultForm, DeleteFightForm, EventForm
from .models import Fight, Pick, Event, User
from .extensions import db
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os

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
        new_event = Event(name=form.name.data)
        db.session.add(new_event)
        db.session.commit()
        flash("Event created successfully!", "success")
        return redirect(url_for('main.dashboard'))
    return render_template('add_event.html', form=form)

@admin.route('/update_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def update_event(event_id):
    if not current_user.is_admin:
        flash("Unauthorized", "danger")
        return redirect(url_for('main.dashboard'))

    event = Event.query.get_or_404(event_id)
    form = EventForm(obj=event)
    print(form.errors)

    if form.validate_on_submit():
        event.name = form.name.data
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

@admin.route('/toggle_lock/<int:event_id>', methods=['POST'])
@login_required
def toggle_lock(event_id):
    if not current_user.is_admin:
        flash('Unauthorized', 'danger')
        return redirect(url_for('main.dashboard'))

    event = Event.query.get_or_404(event_id)
    event.is_locked = not event.is_locked
    db.session.commit()

    # ✅ Assign badges when locking the event (after scoring is finalized)
    if event.is_locked:
        from .utils import assign_badges_for_event
        assign_badges_for_event(event.id)

    flash(f"{'Locked' if event.is_locked else 'Unlocked'} picks for {event.name}", 'success')
    return redirect(request.referrer or url_for('main.dashboard'))


@admin.route('/toggle_archive/<int:event_id>', methods=['POST'])
@login_required
def toggle_archive(event_id):
    if not current_user.is_admin:
        abort(403)
    event = Event.query.get_or_404(event_id)
    event.is_archived = not event.is_archived
    db.session.commit()
    flash(f"Event '{event.name}' moved to {'past' if event.is_archived else 'upcoming'} events.", "info")
    return redirect(url_for('main.dashboard'))


@admin.route('/add_fight', methods=['GET', 'POST'])
@login_required
def add_fight():
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for('main.dashboard'))

    events = Event.query.all()
    if not events:
        flash("No events available. Create an event first.", "warning")
        return redirect(url_for('admin.add_event'))

    form = FightForm()
    form.event_id.choices = [(event.id, event.name) for event in events]

    if form.validate_on_submit():
        favorite_name = form.fighter1.data if form.favorite.data == 'fighter1' else form.fighter2.data
        selected_event = Event.query.get(form.event_id.data)

        max_order = db.session.query(db.func.max(Fight.order)).filter_by(event_id=selected_event.id).scalar()
        next_order = (max_order + 1) if max_order is not None else 0

        new_fight = Fight(
            fighter1=form.fighter1.data,
            fighter2=form.fighter2.data,
            fight_rounds=int(form.fight_rounds.data),
            date=form.date.data,
            favorite=favorite_name,
            event=selected_event,
            best_method=form.best_method.data,
            best_round=form.best_round.data,
            order=next_order
        )
        db.session.add(new_fight)
        db.session.commit()

        # ✅ Automatically create Book's pick
        book_user = User.query.filter_by(username='Book').first()
        if book_user:
            book_pick = Pick(
                user_id=book_user.id,
                fight_id=new_fight.id,
                selected_fighter=favorite_name,
                selected_method=form.best_method.data,
                selected_round=form.best_round.data
            )
            db.session.add(book_pick)
            db.session.commit()
        else:
            flash("Book user not found. Book pick not created.", "warning")

        flash("Fight added successfully!", "success")
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        print("Form submitted with POST")
        print("Form errors:", form.errors)

    return render_template('add_fight.html', form=form)

@admin.route('/fight/<int:fight_id>/update', methods=['GET', 'POST'])
@login_required
def update_fight(fight_id):
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for('main.dashboard'))

    fight = Fight.query.get_or_404(fight_id)
    form = FightForm()
    events = Event.query.all()

    form.event_id.choices = [(event.id, event.name) for event in events]

    if request.method == 'GET':
        form.fighter1.data = fight.fighter1
        form.fighter2.data = fight.fighter2
        form.date.data = fight.date
        form.favorite.data = 'fighter1' if fight.favorite == fight.fighter1 else 'fighter2'
        form.event_id.data = fight.event_id
        form.best_method.data = fight.best_method
        form.best_round.data = fight.best_round
        form.fight_rounds.data = str(fight.fight_rounds)
        form.order.data = fight.order if hasattr(form, 'order') else None

    if form.validate_on_submit():
        fight.fighter1 = form.fighter1.data
        fight.fighter2 = form.fighter2.data
        fight.date = form.date.data
        fight.favorite = form.fighter1.data if form.favorite.data == 'fighter1' else form.fighter2.data
        fight.event_id = form.event_id.data
        fight.best_method = form.best_method.data
        fight.best_round = form.best_round.data
        fight.fight_rounds = int(form.fight_rounds.data)
        if hasattr(form, 'order'):
            fight.order = form.order.data

        db.session.commit()

        # 🧠 Update Book user’s pick
        book_user = User.query.filter_by(username="Book").first()
        if book_user:
            book_pick = Pick.query.filter_by(user_id=book_user.id, fight_id=fight.id).first()
            if book_pick:
                book_pick.selected_fighter = fight.favorite
                book_pick.selected_method = fight.best_method
                book_pick.selected_round = fight.best_round
                db.session.commit()

        flash("Fight updated successfully!", "success")
        return redirect(url_for('main.dashboard'))

    return render_template('update_fight.html', form=form, fight=fight)


@admin.route('/reorder_fights/<int:event_id>', methods=['GET', 'POST'])
@login_required
def reorder_fights(event_id):
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for('main.dashboard'))

    event = Event.query.get_or_404(event_id)
    fights = Fight.query.filter_by(event_id=event.id).order_by(Fight.order.asc()).all()

    if request.method == 'POST':
        new_order = request.form.getlist('fight_order')
        for index, fight_id in enumerate(new_order):
            fight = Fight.query.get(int(fight_id))
            fight.order = index
        db.session.commit()
        flash("Fights reordered successfully!", "success")
        return redirect(url_for('main.dashboard'))

    return render_template('reorder_fights.html', event=event, fights=fights)


@admin.route('/fight/<int:fight_id>/result', methods=['GET', 'POST'])
@login_required
def fight_result(fight_id):
    if not is_admin():
        flash("Access denied", "danger")
        return redirect(url_for('main.dashboard'))

    fight = Fight.query.get_or_404(fight_id)
    form = FightResultForm()
    form.winner.choices = [(fight.fighter1, fight.fighter1), (fight.fighter2, fight.fighter2)]

    # Dynamically set round choices based on fight config
    form.round.choices = [(str(i), f"Round {i}") for i in range(1, fight.fight_rounds + 1)]
    form.best_round.choices = [(str(i), f"Round {i}") for i in range(1, fight.fight_rounds + 1)]

    if fight.method != 'Decision':
        if 'Decision' not in [choice[0] for choice in form.round.choices]:
            form.round.choices.append(('Decision', 'Decision'))
        if 'Decision' not in [choice[0] for choice in form.best_round.choices]:
            form.best_round.choices.append(('Decision', 'Decision'))

    if request.method == 'GET':
        form.winner.data = fight.winner if fight.winner else fight.favorite
        form.method.data = fight.method if fight.method else fight.best_method
        form.round.data = fight.round if fight.round else fight.best_round
        form.best_method.data = fight.best_method
        form.best_round.data = fight.best_round

    if form.validate_on_submit():
        if form.method.data == 'Decision' and form.round.data != 'Decision':
            form.round.errors.append("Round must be 'Decision' when method is 'Decision'.")
            return render_template('fight_result.html', fight=fight, form=form)

        if form.method.data != 'Decision' and form.round.data == 'Decision':
            form.round.errors.append("'Decision' round is only allowed when method is 'Decision'.")
            return render_template('fight_result.html', fight=fight, form=form)

        fight.winner = form.winner.data
        fight.method = form.method.data
        fight.round = form.round.data
        fight.best_method = form.best_method.data
        fight.best_round = form.best_round.data
        db.session.commit()

        # Always recalculate points after saving
        picks = Pick.query.filter_by(fight_id=fight.id).all()
        for pick in picks:
            points = 0
            correct_winner = pick.selected_fighter == fight.winner
            correct_method = fight.method and pick.selected_method == fight.method
            correct_round = fight.round and pick.selected_round == fight.round
            is_underdog = pick.selected_fighter != fight.favorite

            if correct_winner:
                points += 1
                if correct_method:
                    points += 1
                if correct_round:
                    points += 1

                if correct_method and correct_round:
                    points += 2  # bonus for perfect pick

                if is_underdog:
                    points *= 2

            pick.points_awarded = points

        # Book user logic
        book_user = User.query.filter_by(username='Book').first()
        if not book_user:
            book_user = User(book_user = User(
            username=os.getenv('BOOK_USERNAME'),
            email=os.getenv('BOOK_EMAIL'),
            is_admin=False,
            is_verified=True))
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

        book_points = 0
        correct_book_winner = book_pick.selected_fighter == fight.winner
        correct_book_method = fight.method and book_pick.selected_method == fight.method
        correct_book_round = fight.round and book_pick.selected_round == fight.round
        book_is_underdog = book_pick.selected_fighter != fight.favorite

        if correct_book_winner:
            book_points += 1
            if correct_book_method:
                book_points += 1
            if correct_book_round:
                book_points += 1

            if correct_book_method and correct_book_round:
                book_points += 2  # bonus for perfect book pick

            if book_is_underdog:
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