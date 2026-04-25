from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="operator")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Warehouse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text)
    items = db.relationship("Item", backref="warehouse", lazy=True)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    purchase_price = db.Column(db.Float, default=0)
    sale_price = db.Column(db.Float, default=0)
    unit_profit = db.Column(db.Float, default=0)
    quantity = db.Column(db.Integer, default=0)
    reorder_level = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouse.id"), nullable=False)
class StockMovement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    movement_type = db.Column(db.String(10), nullable=False)
    note = db.Column(db.Text)

    item = db.relationship("Item", backref="movements")

from datetime import datetime

from datetime import datetime

class SalesInvoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(150), nullable=False)
    customer_phone = db.Column(db.String(50))
    notes = db.Column(db.Text)
    payment_method = db.Column(db.String(50), default="cash")
    amount_paid = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    is_finalized = db.Column(db.Boolean, default=False)
    finalized_at = db.Column(db.DateTime, nullable=True)

    items = db.relationship(
        "SalesInvoiceItem",
        backref="invoice",
        cascade="all, delete-orphan",
        lazy=True
    )

    @property
    def balance_due(self):
        return max((self.total_amount or 0) - (self.amount_paid or 0), 0)

    @property
    def payment_status(self):
        if (self.amount_paid or 0) >= (self.total_amount or 0):
            return "مدفوعة"
        if (self.amount_paid or 0) > 0:
            return "مدفوعة جزئيًا"
        return "غير مدفوعة"

class SalesInvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("sales_invoice.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    sale_price = db.Column(db.Float, nullable=False, default=0)
    line_total = db.Column(db.Float, nullable=False, default=0)

    item = db.relationship("Item", backref="invoice_lines")

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    slug = db.Column(db.String(120), nullable=False, unique=True)

    products = db.relationship("Product", backref="category", lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)

    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False, unique=True)
    short_description = db.Column(db.String(300))
    description = db.Column(db.Text)

    image_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)

    item = db.relationship("Item", backref="product_entry")

from datetime import datetime
from app import db

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(200), nullable=False)
    customer_phone = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default="pending", nullable=False)
    total_amount = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    invoice_id = db.Column(db.Integer, db.ForeignKey("sales_invoice.id"), nullable=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    payment_status = db.Column(db.String(50), default="paid", nullable=False)
    commission = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")

    @property
    def status_label(self):
        labels = {
            "pending": "قيد الانتظار",
            "confirmed": "تم التأكيد",
            "shipping": "قيد التوصيل",
            "completed": "مكتمل",
        }
        return labels.get(self.status, self.status)

    @property
    def payment_status_label(self):
        labels = {
            "paid": "مدفوع",
            "pending": "معلق",
        }
        return labels.get(self.payment_status, self.payment_status)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    price = db.Column(db.Float, default=0, nullable=False)
    product = db.relationship("Product")
    @property
    def line_total(self):
        return (self.quantity or 0) * (self.price or 0)

