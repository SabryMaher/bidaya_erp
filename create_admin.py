from app import create_app, db, bcrypt
from app.models import User

app = create_app()

with app.app_context():
    db.create_all()

    user = User.query.filter_by(email="admin@bidaya.com").first()
    if user:
        db.session.delete(user)
        db.session.commit()

    hashed = bcrypt.generate_password_hash("123456").decode("utf-8")

    user = User(
        username="admin",
        email="admin@bidaya.com",
        password=hashed,
        role="owner"
    )

    db.session.add(user)
    db.session.commit()
    print("admin created")