from app import create_app, db
from app.models import Item, Warehouse, Category, Product

app = create_app()

def make_slug(text):
    return str(text).strip().replace(" ", "-").lower()

with app.app_context():
    warehouses = Warehouse.query.all()
    for warehouse in warehouses:
        slug = make_slug(warehouse.name)

        # 👇 نتحقق بالاسم أو slug
        exists = Category.query.filter(
            (Category.slug == slug) | (Category.name == warehouse.name)
        ).first()

        if not exists:
            db.session.add(Category(
                name=warehouse.name,
                slug=slug
            ))
    db.session.commit()

    categories_map = {c.name: c for c in Category.query.all()}
    existing_item_ids = {p.item_id for p in Product.query.all()}

    for item in Item.query.all():
        if item.id in existing_item_ids:
            continue

        category = categories_map.get(item.warehouse.name) if item.warehouse else None

        product = Product(
            item_id=item.id,
            category_id=category.id if category else None,
            title=item.name,
            slug=f"product-{item.id}",
            short_description=item.description or item.name,
            description=item.description or item.name,
            image_url="https://via.placeholder.com/500x400?text=Product",
            is_active=True,
            is_featured=True if item.id <= 8 else False,
        )
        db.session.add(product)

    db.session.commit()
    print("Shop categories and products synced successfully")