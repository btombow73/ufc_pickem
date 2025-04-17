from flask import url_for, current_app
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from .app import mail
from werkzeug.utils import secure_filename
from PIL import Image
import os
from .models import User, UserBadge, Badge, db


def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirm')

def confirm_verification_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=expiration)
    except Exception:
        return False
    return email




def send_verification_email(user):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = s.dumps({'user_id': user.id})
    link = url_for('auth.verify_email', token=token, _external=True)

    msg = Message('Verify Your Email', recipients=[user.email])
    msg.body = f'Hi {user.username},\n\nPlease verify your email by clicking the link below:\n{link}\n\nIf you did not register, please ignore this email.'
    mail.send(msg)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def safe_float(val):
    try:
        if isinstance(val, str) and '%' in val:
            return float(val.strip('%')) / 100
        return float(val)  # Convert to float
    except (ValueError, TypeError):
        return 0.0  # Return 0 if there's an issue with conversion

def resize_and_save_avatar(file, user_id):
    filename = secure_filename(f"user_{user_id}.png")
    filepath = os.path.join('static', 'uploads', filename)

    image = Image.open(file)
    image = image.convert("RGB")
    image.thumbnail((300, 300))
    image.save(filepath, format='PNG')
    return filename

def evaluate_badges_for_user(user, event_id=None):
    """Evaluate which badges a user qualifies for in a given event or overall."""
    from .models import Badge, UserBadge, Event

    badges_to_award = []

    # Filter the user's picks to the specified event (or all picks if event_id is None)
    picks = user.picks
    if event_id:
        picks = [p for p in picks if p.fight and p.fight.event_id == event_id]
    if not picks or len(picks) == 0:
        return []  # No picks means no badges from picks

    # Calculate basic stats for this set of picks
    total_picks = len(picks)
    correct_winner_count = sum(
        1 for p in picks 
        if p.fight and p.fight.winner and p.selected_fighter == p.fight.winner
    )
    # "perfect" means fully correct pick (winner+method+round)
    perfect_picks_count = sum(
        1 for p in picks if (
            p.fight and p.fight.winner and 
            p.selected_fighter == p.fight.winner and 
            p.selected_method == p.fight.method and 
            p.selected_round == p.fight.round
        )
    )
    incorrect_count = total_picks - correct_winner_count
    accuracy = correct_winner_count / total_picks if total_picks > 0 else 0.0

    # Count correct underdog picks (where the picked fighter was not the favorite but won)
    correct_underdog_count = sum(
        1 for p in picks if (
            p.fight and p.fight.winner and 
            p.selected_fighter == p.fight.winner and 
            p.fight.favorite and p.selected_fighter != p.fight.favorite
        )
    )

    # Determine if this event is the user's first event (for Rookie badge).
    is_first_event = False
    if event_id:
        # Check if user has picks in any other event
        other_events = {p.fight.event_id for p in user.picks if p.fight and p.fight.event_id != event_id}
        if len(other_events) == 0:
            is_first_event = True

    # Badge criteria checks (event-specific performance)
    # Each tuple: (badge_name, condition_boolean)
    badge_criteria = [
        ("Flawless Victory 🧼", accuracy == 1.0 and total_picks >= 3),
        ("Perfect Picker 🎯", perfect_picks_count >= 3),
        ("Sharp Shooter 🔫", accuracy >= 0.6 and accuracy < 1.0),
        ("Glass Jaw 🫠", accuracy < 0.3 and total_picks >= 3),
        ("Reverse Oracle 🔮", incorrect_count >= 5),
        ("Just Stop 🛑", total_picks >= 10 and correct_winner_count == 0),
        ("Beginner's Luck 🍀", total_picks == 1 and correct_winner_count == 1),
        ("Upset Specialist 😱", correct_underdog_count >= 3)
    ]
    if is_first_event:
        # If this is the user's first-ever event participation
        badge_criteria.append(("Rookie 🐣", True))

    # Fetch each badge template (event_id=None) and check if the user already has it
    for badge_name, condition in badge_criteria:
        if not condition:
            continue
        # Find the badge definition (template) by name
        badge_def = Badge.query.filter_by(name=badge_name, event_id=None).first()
        if not badge_def:
            # If somehow the badge definition is not in DB, skip (or create if desired)
            continue
        # Check if the user already has this badge (in any event or globally)
        already_has = (UserBadge.query.join(Badge)
                       .filter(UserBadge.user_id == user.id, Badge.name == badge_name)
                       .first())
        if already_has:
            continue
        # If not already awarded, add the badge template to the list
        badges_to_award.append(badge_def)

    return badges_to_award


def assign_badges_for_event(event_id):
    """Evaluate and assign all relevant badges for a specific event to all users."""
    from .models import User, UserBadge, Badge, Event, db
    from sqlalchemy.orm import joinedload

    event = Event.query.get(event_id)
    if not event:
        print(f"Event ID {event_id} not found.")
        return

    # Load all users with their picks for this event in one go
    users = User.query.options(joinedload(User.picks)).all()
    if not users:
        print("No users found to evaluate badges.")
        return

    print(f"🏅 Assigning badges for Event ID {event_id} ({event.name}) to {len(users)} users...")

    # First, determine event ranking for Champion, Runner-Up, Third Place, and Wooden Spoon.
    user_scores = []
    for user in users:
        # Sum points_awarded for this event's picks (points_awarded is set when event results are locked)
        total_points = 0
        for pick in user.picks:
            if pick.fight and pick.fight.event_id == event_id:
                total_points += getattr(pick, "points_awarded", 0)
        if total_points > 0 or any(pick.fight and pick.fight.event_id == event_id for pick in user.picks):
            # Include user if they participated (even if score 0)
            user_scores.append((user, total_points))
    # If no one participated in this event, nothing to do
    if not user_scores:
        print("No picks found for this event, skipping badge assignment.")
        return

    # Sort users by score descending to determine placements
    user_scores.sort(key=lambda x: x[1], reverse=True)
    # Determine top scores for 1st, 2nd, 3rd, and last
    scores = [score for _, score in user_scores]
    unique_scores = sorted(set(scores), reverse=True)
    top_score = unique_scores[0] if unique_scores else None
    second_score = unique_scores[1] if len(unique_scores) > 1 else None
    third_score = unique_scores[2] if len(unique_scores) > 2 else None
    last_score = unique_scores[-1] if unique_scores else None

    # Prepare a dictionary of additional badges to award per user (by user id) for ranking
    rank_badges_award = {user.id: [] for user, _ in user_scores}

    for user, score in user_scores:
        # Champion badge for top score
        if top_score is not None and score == top_score:
            rank_badges_award[user.id].append("Event Champion 🏆")
        # Runner-Up for second place
        if second_score is not None and score == second_score:
            rank_badges_award[user.id].append("Runner-Up 🥈")
        # Third Place for third
        if third_score is not None and score == third_score:
            rank_badges_award[user.id].append("Third Place 🥉")
        # Wooden Spoon for last place
        if last_score is not None and score == last_score:
            rank_badges_award[user.id].append("Wooden Spoon 🥄")

    # Now evaluate individual performance-based badges for each user (using the previous function)
    for user in users:
        # Only evaluate if user participated in this event (to avoid awarding things like Regular to non-participants here)
        if not any(pick.fight and pick.fight.event_id == event_id for pick in user.picks):
            continue

        # Evaluate event-specific performance badges and participation badges
        earned_templates = evaluate_badges_for_user(user, event_id=event_id)  # returns template Badge objects

        # Collect names of badges from templates (for consistent handling below)
        earned_names = [badge.name for badge in earned_templates]

        # Include any rank-based badges determined above
        for badge_name in rank_badges_award.get(user.id, []):
            # Ensure we avoid duplicates (if by some logic it was already in earned_names, though that shouldn't happen for rank vs performance)
            if badge_name not in earned_names:
                earned_names.append(badge_name)
                # Fetch the template Badge for this name
                badge_def = Badge.query.filter_by(name=badge_name, event_id=None).first()
                if badge_def:
                    earned_templates.append(badge_def)

        # Include participation milestones (Regular, Veteran) and legendary streak badges if reached **after** this event
        # Calculate total events participated by user up to this event (inclusive)
        user_event_ids = {p.fight.event_id for p in user.picks if p.fight}
        total_events_participated = len(user_event_ids)
        # Regular (5 events) milestone
        if total_events_participated >= 5:
            badge_name = "Regular 📅"
            badge_def = Badge.query.filter_by(name=badge_name, event_id=None).first()
            if badge_def:
                # If user doesn't have it yet, and this event caused them to reach milestone
                has_badge = UserBadge.query.filter_by(user_id=user.id, badge_id=badge_def.id).first()
                if not has_badge:
                    earned_templates.append(badge_def)
                    earned_names.append(badge_name)
        # Veteran (20 events) milestone
        if total_events_participated >= 20:
            badge_name = "Veteran 🎖️"
            badge_def = Badge.query.filter_by(name=badge_name, event_id=None).first()
            if badge_def:
                has_badge = UserBadge.query.filter_by(user_id=user.id, badge_id=badge_def.id).first()
                if not has_badge:
                    earned_templates.append(badge_def)
                    earned_names.append(badge_name)

        # Legendary badges for event wins (to be awarded when thresholds met)
        # Count total event wins (Champion badges) this user has *before* this event
        badge_champion_template = Badge.query.filter_by(name="Event Champion 🏆", event_id=None).first()
        prev_wins = 0
        if badge_champion_template:
            # Count UserBadge where badge name is "Event Champion 🏆"
            prev_wins = (UserBadge.query.join(Badge)
                         .filter(UserBadge.user_id == user.id, Badge.name == "Event Champion 🏆", Badge.event_id.isnot(None))
                         .count())
        # If this user won the current event, increment their win count
        won_current_event = (top_score is not None and user in [u for u, s in user_scores if s == top_score])
        current_wins = prev_wins + (1 if won_current_event else 0)

        if won_current_event:
            # Check for Triple Crown (3 consecutive wins)
            # We need to see if this user also won the two previous events
            prev_event_win1 = None
            prev_event_win2 = None
            if event_id >= 2:
                prev_event_win1 = UserBadge.query.join(Badge).filter(
                    UserBadge.user_id == user.id,
                    Badge.name == "Event Champion 🏆",
                    Badge.event_id == event_id - 1
                ).first()
            if event_id >= 3:
                prev_event_win2 = UserBadge.query.join(Badge).filter(
                    UserBadge.user_id == user.id,
                    Badge.name == "Event Champion 🏆",
                    Badge.event_id == event_id - 2
                ).first()
            if prev_event_win1 and prev_event_win2:
                # Won three in a row (event_id-2, event_id-1, event_id)
                badge_name = "Triple Crown 👑"
                badge_def = Badge.query.filter_by(name=badge_name, event_id=None).first()
                if badge_def:
                    has_badge = UserBadge.query.filter_by(user_id=user.id, badge_id=badge_def.id).first()
                    if not has_badge:
                        earned_templates.append(badge_def)
                        earned_names.append(badge_name)
        # Check total wins milestones (5 wins, 10 wins)
        if current_wins >= 5:
            badge_name = "Undisputed Champion 💪"
            badge_def = Badge.query.filter_by(name=badge_name, event_id=None).first()
            if badge_def:
                has_badge = UserBadge.query.filter_by(user_id=user.id, badge_id=badge_def.id).first()
                if not has_badge:
                    earned_templates.append(badge_def)
                    earned_names.append(badge_name)
        if current_wins >= 10:
            badge_name = "GOAT 🐐"
            badge_def = Badge.query.filter_by(name=badge_name, event_id=None).first()
            if badge_def:
                has_badge = UserBadge.query.filter_by(user_id=user.id, badge_id=badge_def.id).first()
                if not has_badge:
                    earned_templates.append(badge_def)
                    earned_names.append(badge_name)

        # Now we have a list of badge templates the user earned (earned_templates).
        # For each, assign the badge (create UserBadge entry, and create event-specific Badge if applicable).
        for badge_def in earned_templates:
            # Determine if this badge should be event-specific or not
            if badge_def.event_id is None:
                # Template badge. 
                # If this badge represents an event-specific achievement (like Champion, Flawless, etc.), 
                # we will create a copy tied to this event. Otherwise, we award the badge itself.
                badge_name = badge_def.name
                event_specific = True  # default assume event-specific, then filter out all-time ones
                # Treat participation milestones and legendary multi-event badges as all-time (not event-specific)
                if badge_name in ["Regular 📅", "Veteran 🎖️", "Triple Crown 👑", "Undisputed Champion 💪", "GOAT 🐐", "Season Champion 🏆", "Season Runner-Up 🥈", "Season Third 🥉", "Rookie 🐣"]:
                    event_specific = False
                if not event_id:
                    # If no specific event context, treat as all-time
                    event_specific = False

                if event_specific and event_id:
                    # Create/find a Badge entry specific to this event
                    event_badge = Badge.query.filter_by(name=badge_name, event_id=event_id).first()
                    if not event_badge:
                        # Create a new Badge for this event
                        event_badge = Badge(
                            name=badge_name,
                            icon=badge_def.icon,
                            difficulty=badge_def.difficulty,
                            description=badge_def.description,  # you could append event info here if desired
                            event_id=event_id
                        )
                        db.session.add(event_badge)
                        db.session.flush()  # get id for the new badge
                    # Now link the user to this event-specific badge
                    already_awarded = UserBadge.query.filter_by(user_id=user.id, badge_id=event_badge.id).first()
                    if not already_awarded:
                        db.session.add(UserBadge(user_id=user.id, badge_id=event_badge.id))
                else:
                    # All-time badge: award the template badge itself (event_id=None badge)
                    already_awarded = UserBadge.query.filter_by(user_id=user.id, badge_id=badge_def.id).first()
                    if not already_awarded:
                        db.session.add(UserBadge(user_id=user.id, badge_id=badge_def.id))
            else:
                # If badge_def already has an event_id (which shouldn't happen here since earned_templates are templates), just ensure user_badge exists
                already_awarded = UserBadge.query.filter_by(user_id=user.id, badge_id=badge_def.id).first()
                if not already_awarded:
                    db.session.add(UserBadge(user_id=user.id, badge_id=badge_def.id))

    # Commit all the new UserBadge (and Badge) records to the database
    db.session.commit()
    print(f"✅ Completed badge assignment for Event ID {event_id} ({event.name}).")

