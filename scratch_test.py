from app import create_app, db
from app.models import Item, Warehouse, Category, Product

app = create_app()

with app.app_context():
    print("Categories:", Category.query.count())
    print("Products:", Product.query.count())
    print("Items:", Item.query.count())
    print("Warehouses:", Warehouse.query.count())
