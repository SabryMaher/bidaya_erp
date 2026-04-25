import requests
session = requests.Session()
# Assuming we have an admin user. We can find one in the DB.
from app import db, create_app
from app.models import User
app = create_app()
with app.app_context():
    user = User.query.first()
    print("User email:", user.email if user else "No user")

