from ufc_pickem import create_app
from ufc_pickem.extensions import db  # ✅ import from correct location
from ufc_pickem.models import User
from werkzeug.security import generate_password_hash
from datetime import datetime

# Create the app instance
app = create_app()

# Create the admin user inside app context
with app.app_context():
    existing_user = User.query.filter_by(username='bt012314').first()

    if existing_user:
        print("ℹ️ Admin user already exists.")
    else:
        admin_user = User(
            username='bt012314',
            email='bt012314@gmail.com',
            password=generate_password_hash('Tigers73!'),
            is_admin=True,
            created_at=datetime.utcnow()
        )
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Admin user created successfully.")
