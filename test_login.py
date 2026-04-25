import requests
session = requests.Session()
# First get the CSRF token from the login page
response = session.get("http://127.0.0.1:5000/login")
from bs4 import BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')
csrf_token = soup.find('input', {'name': 'csrf_token'})['value']

# Now try to login. Let's see if we have an admin user in DB
from app import db, create_app
from app.models import User
app = create_app()
with app.app_context():
    user = User.query.first()
    email = user.email if user else "admin@bidaya.com"
    # We don't know the password, but we can bypass or just check the user

print("Found user:", email)
