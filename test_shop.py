import requests
from app import create_app

app = create_app()
with app.app_context():
    with app.test_client() as client:
        response = client.get('/shop')
        print(f"Status Code: {response.status_code}")
        if response.status_code != 200:
            print("Error parsing /shop")
        else:
            print("/shop loaded successfully")
