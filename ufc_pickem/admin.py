from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from .forms import FightForm, FightResultForm, DeleteFightForm, EventForm
from .models import Fight, Pick, Event
from .app import db
from .extensions import db


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
    # Set event choices dynamically
    form.event_id.choices = [(event.id, event.name) for event in events]
    if form.validate_on_submit():
        # Determine favorite fighter's name based on selection (fighter1 or fighter2)
        favorite_name = form.fighter1.data if form.favorite.data == 'fighter1' else form.fighter2.data
        event = Event.query.get(form.event_id.data)
        new_fight = Fight(
            fighter1=form.fighter1.data,
            fighter2=form.fighter2.data,
            date=form.date.data,
            favorite=favorite_name,
            event=event
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
        # Pre-fill form fields with existing fight data
        form.fighter1.data = fight.fighter1
        form.fighter2.data = fight.fighter2
        form.date.data = fight.date
        form.favorite.data = 'fighter1' if fight.favorite == fight.fighter1 else 'fighter2'
        form.event_id.data = fight.event_id
    if form.validate_on_submit():
        # Update fight details
        fight.fighter1 = form.fighter1.data
        fight.fighter2 = form.fighter2.data
        fight.date = form.date.data
        fight.favorite = form.fighter1.data if form.favorite.data == 'fighter1' else form.fighter2.data
        fight.event_id = form.event_id.data
        db.session.commit()
        # If a result was already recorded and we changed something like favorite, recalc points
        if fight.winner:
            picks = Pick.query.filter_by(fight_id=fight.id).all()
            for pick in picks:
                points = 0
                if pick.selected_fighter == fight.winner:
                    points = 1
                    if fight.method and pick.selected_method == fight.method:
                        points += 1
                    if fight.favorite and fight.winner != fight.favorite:
                        points *= 2
                pick.points_awarded = points
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
    # Set winner choices to the two fighters for this fight
    form.winner.choices = [(fight.fighter1, fight.fighter1), (fight.fighter2, fight.fighter2)]
    if request.method == 'GET' and fight.winner:
        # Pre-fill result form if a result exists (to allow editing)
        form.winner.data = fight.winner
        form.method.data = fight.method
    if form.validate_on_submit():
        fight.winner = form.winner.data
        fight.method = form.method.data
        db.session.commit()
        flash("Fight result recorded!", "success")
        # Update points for all picks on this fight based on the new result
        picks = Pick.query.filter_by(fight_id=fight.id).all()
        for pick in picks:
            points = 0
            if pick.selected_fighter == fight.winner:
                points = 1  # base point for correct winner
                if fight.method and pick.selected_method == fight.method:
                    points += 1  # bonus point for correct method
                if fight.favorite and fight.winner != fight.favorite:
                    points *= 2  # double points if underdog win
            pick.points_awarded = points
        db.session.commit()
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
        # First delete all picks associated with this fight, then delete the fight
        Pick.query.filter_by(fight_id=fight.id).delete()
        db.session.delete(fight)
        db.session.commit()
        flash("Fight deleted successfully.", 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('delete_fight.html', fight=fight, form=form)
