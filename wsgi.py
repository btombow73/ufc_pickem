from ufc_pickem import create_app
from flask_migrate import upgrade

app = create_app()

# Run migrations on startup
with app.app_context():
    upgrade()