from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from app.models import User, Warehouse, Item, StockMovement
from app.forms import LoginForm, WarehouseForm, ItemForm

from sqlalchemy import func, desc
from datetime import datetime, timedelta
from flask import request, render_template, redirect, url_for, flash, Response
import csv
from io import StringIO

from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from sqlalchemy import or_

from flask import request, render_template, redirect, url_for, flash, Response
from datetime import datetime, timedelta
from sqlalchemy import func, desc

from app.models import User, Warehouse, Item, StockMovement, SalesInvoice, SalesInvoiceItem, Category, Product, Order, OrderItem
from app.forms import LoginForm, WarehouseForm, ItemForm, SalesInvoiceForm, SalesInvoiceItemForm
from flask import render_template, redirect, url_for, flash, request
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from app.models import (
    User,
    Warehouse,
    Item,
    StockMovement,
    SalesInvoice,
    SalesInvoiceItem,
    Order,
    OrderItem,
    Product,
)
from app.forms import (
    LoginForm,
    WarehouseForm,
    ItemForm,
    SalesInvoiceForm,
    SalesInvoiceItemForm,
)

from functools import wraps

from datetime import datetime

from app.models import User, Warehouse, Item, StockMovement, SalesInvoice, SalesInvoiceItem, Category, Product
from flask import render_template, redirect, url_for, flash, request

from flask import session, redirect, url_for

def register_routes(app):

    def role_required(*allowed_roles):
        def decorator(view_func):
            @wraps(view_func)
            def wrapped_view(*args, **kwargs):
                if not current_user.is_authenticated:
                    return redirect(url_for("login"))
                if getattr(current_user, "role", "") not in allowed_roles:
                    flash("ليس لديك صلاحية الوصول لهذه الصفحة", "danger")
                    return redirect(url_for("dashboard"))
                return view_func(*args, **kwargs)
            return wrapped_view
        return decorator

    @app.route("/")
    def home():
        return redirect(url_for("dashboard"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                next_page = request.args.get("next")
                return redirect(next_page) if next_page else redirect(url_for("dashboard"))
            flash("بيانات الدخول غير صحيحة", "danger")
        return render_template("login.html", form=form)

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        warehouse_count = Warehouse.query.count()
        item_count = Item.query.count()
        low_stock_count = Item.query.filter(Item.quantity <= Item.reorder_level).count()
        alerts = get_system_alerts()
        today = datetime.utcnow().date()
        tomorrow = today + timedelta(days=1)
        start_week = today - timedelta(days=today.weekday())

        today_sales = (
            db.session.query(func.sum(SalesInvoice.total_amount))
            .filter(SalesInvoice.created_at >= today)
            .filter(SalesInvoice.created_at < tomorrow)
            .scalar()
            or 0
        )

        today_orders = (
            db.session.query(func.count(Order.id))
            .filter(Order.created_at >= today)
            .filter(Order.created_at < tomorrow)
            .scalar()
            or 0
        )

        week_sales = (
            db.session.query(func.sum(SalesInvoice.total_amount))
            .filter(SalesInvoice.created_at >= start_week)
            .scalar()
            or 0
        )

        week_orders = (
            db.session.query(func.count(Order.id))
            .filter(Order.created_at >= start_week)
            .scalar()
            or 0
        )
        return render_template(
            "dashboard.html",
            warehouse_count=warehouse_count,
            item_count=item_count,
            low_stock_count=low_stock_count,
            alerts=alerts,
            today_sales=today_sales,
            today_orders=today_orders,
            week_sales=week_sales,
            week_orders=week_orders,
        )

    @app.route("/warehouses", methods=["GET", "POST"])
    @login_required
    def warehouses():
        form = WarehouseForm()
        q = request.args.get("q", "").strip()

        if form.validate_on_submit():
            warehouse = Warehouse(
                name=form.name.data,
                category=form.category.data,
                notes=form.notes.data
            )
            db.session.add(warehouse)
            db.session.commit()

            def make_slug(text):
                return str(text).strip().replace(" ", "-").lower()

            slug = make_slug(warehouse.category)
            exists = Category.query.filter(
                (Category.slug == slug) | (Category.name == warehouse.category)
            ).first()
            if not exists:
                new_cat = Category(name=warehouse.category, slug=slug)
                db.session.add(new_cat)
                db.session.commit()

            flash("تم إضافة المخزن بنجاح", "success")
            return redirect(url_for("warehouses"))

        query = Warehouse.query
        if q:
            query = query.filter(
                Warehouse.name.contains(q) | Warehouse.category.contains(q)
            )

        all_warehouses = query.order_by(Warehouse.id.desc()).all()
        return render_template("warehouses.html", form=form, warehouses=all_warehouses, q=q)

    @app.route("/warehouses/<int:warehouse_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_warehouse(warehouse_id):
        warehouse = Warehouse.query.get_or_404(warehouse_id)
        form = WarehouseForm(obj=warehouse)

        if form.validate_on_submit():
            warehouse.name = form.name.data
            warehouse.category = form.category.data
            warehouse.notes = form.notes.data
            db.session.commit()

            def make_slug(text):
                return str(text).strip().replace(" ", "-").lower()

            slug = make_slug(warehouse.category)
            exists = Category.query.filter(
                (Category.slug == slug) | (Category.name == warehouse.category)
            ).first()
            if not exists:
                new_cat = Category(name=warehouse.category, slug=slug)
                db.session.add(new_cat)
                db.session.commit()

            flash("تم تعديل المخزن بنجاح", "success")
            return redirect(url_for("warehouses"))

        return render_template("warehouses.html", form=form, warehouses=Warehouse.query.order_by(Warehouse.id.desc()).all(), edit_mode=True, warehouse_obj=warehouse, q="")

    @app.route("/warehouses/<int:warehouse_id>/delete", methods=["POST"])
    @login_required
    def delete_warehouse(warehouse_id):
        warehouse = Warehouse.query.get_or_404(warehouse_id)

        if warehouse.items and len(warehouse.items) > 0:
            flash("لا يمكن حذف مخزن يحتوي على أصناف", "danger")
            return redirect(url_for("warehouses"))

        db.session.delete(warehouse)
        db.session.commit()
        flash("تم حذف المخزن", "success")
        return redirect(url_for("warehouses"))

    @app.route("/items", methods=["GET", "POST"])
    @login_required
    def items():
        form = ItemForm()
        form.warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.order_by(Warehouse.name.asc()).all()]
        q = request.args.get("q", "").strip()

        if form.validate_on_submit():
            item = Item(
                item_code=form.item_code.data,
                name=form.name.data,
                description=form.description.data,
                purchase_price=form.purchase_price.data,
                sale_price=form.sale_price.data,
                unit_profit=form.sale_price.data - form.purchase_price.data,
                quantity=form.quantity.data,
                reorder_level=form.reorder_level.data,
                warehouse_id=form.warehouse_id.data,
                notes=form.notes.data
            )
            db.session.add(item)
            db.session.flush()

            warehouse = Warehouse.query.get(item.warehouse_id)
            if warehouse:
                def make_slug(text):
                    return str(text).strip().replace(" ", "-").lower()
                slug = make_slug(warehouse.category)
                category = Category.query.filter(
                    (Category.slug == slug) | (Category.name == warehouse.category)
                ).first()
                if not category:
                    category = Category(name=warehouse.category, slug=slug)
                    db.session.add(category)
                    db.session.flush()

                product = Product(
                    item_id=item.id,
                    category_id=category.id,
                    title=item.name,
                    slug=f"product-{item.id}",
                    short_description=item.description or item.name,
                    description=item.description or item.name,
                    image_url="https://via.placeholder.com/500x400?text=Product",
                    is_active=True,
                    is_featured=False
                )
                db.session.add(product)

            db.session.commit()
            flash("تم إضافة الصنف بنجاح", "success")
            return redirect(url_for("items"))

        query = Item.query
        if q:
            query = query.filter(
                Item.name.contains(q) | Item.item_code.contains(q) | Item.description.contains(q)
            )

        all_items = query.order_by(Item.id.desc()).all()
        return render_template("items.html", form=form, items=all_items, q=q)

    @app.route("/items/<int:item_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_item(item_id):
        item = Item.query.get_or_404(item_id)
        form = ItemForm(obj=item)
        form.warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.order_by(Warehouse.name.asc()).all()]

        if request.method == "GET":
            form.warehouse_id.data = item.warehouse_id

        if form.validate_on_submit():
            item.item_code = form.item_code.data
            item.name = form.name.data
            item.description = form.description.data
            item.purchase_price = form.purchase_price.data
            item.sale_price = form.sale_price.data
            item.unit_profit = form.sale_price.data - form.purchase_price.data
            item.quantity = form.quantity.data
            item.reorder_level = form.reorder_level.data
            item.warehouse_id = form.warehouse_id.data
            item.notes = form.notes.data

            product = Product.query.filter_by(item_id=item.id).first()
            if product:
                product.title = item.name
                product.short_description = item.description or item.name
                product.description = item.description or item.name
                
                warehouse = Warehouse.query.get(item.warehouse_id)
                if warehouse:
                    def make_slug(text):
                        return str(text).strip().replace(" ", "-").lower()
                    slug = make_slug(warehouse.category)
                    category = Category.query.filter(
                        (Category.slug == slug) | (Category.name == warehouse.category)
                    ).first()
                    if not category:
                        category = Category(name=warehouse.category, slug=slug)
                        db.session.add(category)
                        db.session.flush()
                    product.category_id = category.id

            db.session.commit()
            flash("تم تعديل الصنف بنجاح", "success")
            return redirect(url_for("items"))

        return render_template("items.html", form=form, items=Item.query.order_by(Item.id.desc()).all(), edit_mode=True, item_obj=item, q="")

    @app.route("/items/<int:item_id>/delete", methods=["POST"])
    @login_required
    def delete_item(item_id):
        item = Item.query.get_or_404(item_id)
        
        product = Product.query.filter_by(item_id=item.id).first()
        if product:
            db.session.delete(product)

        db.session.delete(item)
        db.session.commit()
        flash("تم حذف الصنف", "success")
        return redirect(url_for("items"))

    @app.route("/movement", methods=["GET", "POST"])
    @login_required
    def movement():
        from flask import Response
        import csv
        from io import StringIO

        items = Item.query.order_by(Item.name.asc()).all()

        if request.method == "POST":
            item_id = int(request.form.get("item_id"))
            quantity = int(request.form.get("quantity"))
            movement_type = request.form.get("type")
            note = request.form.get("note")

            item = Item.query.get_or_404(item_id)

            if movement_type == "in":
                item.quantity += quantity
            elif movement_type == "out":
                if quantity > item.quantity:
                    flash("لا يمكن صرف كمية أكبر من المتاح", "danger")
                    return redirect(url_for("movement"))
                item.quantity -= quantity

            movement = StockMovement(
                item_id=item.id,
                quantity=quantity,
                movement_type=movement_type,
                note=note
            )

            db.session.add(movement)
            db.session.commit()
            flash("تم تسجيل الحركة بنجاح", "success")
            return redirect(url_for("movement"))

        q = request.args.get("q", "").strip()
        movement_filter = request.args.get("movement_type", "").strip()
        export = request.args.get("export", "").strip()

        query = StockMovement.query.join(Item)

        if q:
            query = query.filter(Item.name.contains(q))

        if movement_filter in ["in", "out"]:
            query = query.filter(StockMovement.movement_type == movement_filter)

        movements = query.order_by(StockMovement.id.desc()).all()

        if export == "csv":
            si = StringIO()
            cw = csv.writer(si)

            cw.writerow(["ID", "الصنف", "نوع الحركة", "الكمية", "ملاحظة"])

            for movement in movements:
                cw.writerow([
                    movement.id,
                    movement.item.name,
                    "إضافة" if movement.movement_type == "in" else "صرف",
                    movement.quantity,
                    movement.note or ""
                ])

            output = si.getvalue()
            return Response(
                output,
                mimetype="text/csv; charset=utf-8",
                headers={"Content-Disposition": "attachment; filename=stock_movements.csv"}
            )

        return render_template(
            "movement.html",
            items=items,
            movements=movements,
            q=q,
            movement_filter=movement_filter
        )
    @app.route("/import-csv")
    @login_required
    def import_csv():
        from app.import_csv import import_from_csv

        try:
            count, skipped, headers = import_from_csv("data.csv")
            flash(f"تم استيراد {count} صنف بنجاح، وتخطي {skipped}", "success")
        except Exception as e:
            flash(str(e), "danger")

        return redirect(url_for("dashboard"))
    
    @app.route("/invoices")
    @login_required
    def invoices():
        all_invoices = SalesInvoice.query.order_by(SalesInvoice.id.desc()).all()
        return render_template("invoices.html", invoices=all_invoices)

    @app.route("/invoices/new", methods=["GET", "POST"])
    @login_required
    def new_invoice():
        form = SalesInvoiceForm()

        if form.validate_on_submit():
            invoice = SalesInvoice(
                customer_name=form.customer_name.data,
                customer_phone=form.customer_phone.data,
                notes=form.notes.data,
                payment_method=form.payment_method.data,
                amount_paid=form.amount_paid.data or 0,
                total_amount=0,
            )
            db.session.add(invoice)
            db.session.commit()
            flash("تم إنشاء الفاتورة بنجاح", "success")
            return redirect(url_for("edit_invoice", invoice_id=invoice.id))

        return render_template("new_invoice.html", form=form)

    @app.route("/invoices/<int:invoice_id>", methods=["GET", "POST"])
    @login_required
    def edit_invoice(invoice_id):
        invoice = SalesInvoice.query.get_or_404(invoice_id)
        item_form = SalesInvoiceItemForm()

        item_form.item_id.choices = [
            (item.id, f"{item.name} | المتاح: {item.quantity} | سعر البيع: {item.sale_price}")
            for item in Item.query.order_by(Item.name.asc()).all()
        ]

        if invoice.is_finalized:
            return render_template("invoice_detail.html", invoice=invoice, item_form=item_form)

        if item_form.validate_on_submit():
            item = Item.query.get_or_404(item_form.item_id.data)
            quantity = item_form.quantity.data

            if quantity > item.quantity:
                flash("الكمية المطلوبة أكبر من المتاح بالمخزون", "danger")
                return redirect(url_for("edit_invoice", invoice_id=invoice.id))

            line = SalesInvoiceItem(
                invoice_id=invoice.id,
                item_id=item.id,
                quantity=quantity,
                sale_price=item.sale_price,
                line_total=item.sale_price * quantity,
            )
            db.session.add(line)

            item.quantity -= quantity

            movement = StockMovement(
                item_id=item.id,
                quantity=quantity,
                movement_type="out",
                note=f"فاتورة بيع رقم {invoice.id}",
            )
            db.session.add(movement)

            db.session.flush()
            invoice.total_amount = sum(line.line_total for line in invoice.items)
            db.session.commit()

            flash("تمت إضافة الصنف للفاتورة", "success")
            return redirect(url_for("edit_invoice", invoice_id=invoice.id))

        invoice.total_amount = sum(line.line_total for line in invoice.items)
        db.session.commit()

        return render_template("invoice_detail.html", invoice=invoice, item_form=item_form)

    @app.route("/invoice-items/<int:line_id>/delete", methods=["POST"])
    @login_required
    def delete_invoice_item(line_id):
        line = SalesInvoiceItem.query.get_or_404(line_id)
        invoice = line.invoice

        if invoice.is_finalized:
            flash("لا يمكن حذف أصناف من فاتورة تم إنهاؤها", "danger")
            return redirect(url_for("edit_invoice", invoice_id=invoice.id))

        item = line.item
        item.quantity += line.quantity

        db.session.delete(line)
        db.session.flush()

        invoice.total_amount = sum(row.line_total for row in invoice.items)
        db.session.commit()

        flash("تم حذف الصنف من الفاتورة", "success")
        return redirect(url_for("edit_invoice", invoice_id=invoice.id))

    @app.route("/invoices/<int:invoice_id>/finalize", methods=["POST"])
    @login_required
    def finalize_invoice(invoice_id):
        invoice = SalesInvoice.query.get_or_404(invoice_id)

        if invoice.is_finalized:
            flash("الفاتورة منتهية بالفعل", "warning")
            return redirect(url_for("edit_invoice", invoice_id=invoice.id))

        if not invoice.items:
            flash("لا يمكن إنهاء فاتورة بدون أصناف", "danger")
            return redirect(url_for("edit_invoice", invoice_id=invoice.id))

        invoice.total_amount = sum(line.line_total for line in invoice.items)
        invoice.is_finalized = True
        invoice.finalized_at = datetime.utcnow()

        db.session.commit()
        flash("تم إنهاء الفاتورة بنجاح", "success")
        return redirect(url_for("edit_invoice", invoice_id=invoice.id))

    @app.route("/invoices/<int:invoice_id>/print")
    @login_required
    def print_invoice(invoice_id):
        invoice = SalesInvoice.query.get_or_404(invoice_id)
        invoice.total_amount = sum(line.line_total for line in invoice.items)
        db.session.commit()
        return render_template("invoice_print.html", invoice=invoice)

    @app.route("/shop")
    def shop_home():
        featured_products = Product.query.filter_by(is_active=True, is_featured=True).limit(8).all()
        latest_products = Product.query.filter_by(is_active=True).order_by(Product.id.desc()).limit(12).all()
        categories = Category.query.order_by(Category.name.asc()).all()

        return render_template(
            "shop/home.html",
            featured_products=featured_products,
            latest_products=latest_products,
            categories=categories
        )


    @app.route("/shop/products")
    def shop_products():
        search = request.args.get("q", "").strip()
        category_slug = request.args.get("category", "").strip()

        categories = Category.query.order_by(Category.name.asc()).all()

        query = Product.query.filter_by(is_active=True)

        if search:
            query = query.filter(Product.title.contains(search))

        if category_slug:
            category = Category.query.filter_by(slug=category_slug).first()
            if category:
                query = query.filter_by(category_id=category.id)

        products = query.order_by(Product.id.desc()).all()

        return render_template(
            "shop/products.html",
            products=products,
            categories=categories,
            current_search=search,
            current_category=category_slug
        )

    @app.route("/shop/product/<slug>")
    def shop_product_detail(slug):
        product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
        related_products = Product.query.filter(
            Product.id != product.id,
            Product.is_active == True
        ).limit(4).all()

        return render_template(
            "shop/product_detail.html",
            product=product,
            related_products=related_products
        )
    @app.route("/cart/add/<int:product_id>", methods=["POST"])
    def add_to_cart(product_id):
        cart = session.get("cart", {})

        if str(product_id) in cart:
            cart[str(product_id)] += 1
        else:
            cart[str(product_id)] = 1

        session["cart"] = cart
        return redirect(url_for("shop_products"))
    
    @app.route("/cart")
    def view_cart():
        cart = session.get("cart", {})
        products = []

        total = 0

        for product_id, qty in cart.items():
            product = Product.query.get(int(product_id))
            if product:
                products.append({
                    "product": product,
                    "qty": qty,
                    "total": qty * (product.item.sale_price if product.item else 0)
                })
                total += qty * (product.item.sale_price if product.item else 0)

        return render_template("shop/cart.html", products=products, total=total)
    
    @app.route("/checkout", methods=["GET", "POST"])
    def checkout():
        if request.method == "POST":
            name = request.form.get("name")
            phone = request.form.get("phone")

            cart = session.get("cart", {})

            order = Order(
                customer_name=name,
                customer_phone=phone,
                order_number=generate_order_number(),
                total_amount=0
            )

            db.session.add(order)
            db.session.flush()

            total = 0

            for product_id, qty in cart.items():
                product = Product.query.get(int(product_id))
                if product:
                    price = product.item.sale_price if product.item else 0

                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        quantity=qty,
                        price=price
                    )

                    db.session.add(order_item)

                    total += price * qty

            order.total_amount = total

            db.session.commit()

            session["cart"] = {}

            return redirect(url_for("order_success", order_number=order.order_number))

        return render_template("shop/checkout.html")

    @app.route("/orders")
    @login_required
    def orders():
        all_orders = Order.query.order_by(Order.id.desc()).all()
        return render_template("shop/orders.html", orders=all_orders)
    
    @app.route("/admin/products")
    @login_required
    def admin_products():
        products = Product.query.all()
        return render_template("shop/admin_products.html", products=products)
    
    @app.route("/admin/products/edit/<int:id>", methods=["GET", "POST"])
    @login_required
    def edit_product(id):
        product = Product.query.get_or_404(id)

        if request.method == "POST":
            product.image_url = request.form.get("image_url")
            product.description = request.form.get("description")
            product.short_description = request.form.get("short_description")

            db.session.commit()
            return redirect("/admin/products")

        return render_template("shop/edit_product.html", product=product)

    @app.route("/cart/remove/<int:product_id>", methods=["POST"])
    def remove_from_cart(product_id):
        cart = session.get("cart", {})
        cart.pop(str(product_id), None)
        session["cart"] = cart
        flash("تم حذف المنتج من السلة", "success")
        return redirect(url_for("view_cart"))    

    @app.route("/orders/<int:order_id>")
    def order_detail(order_id):
        order = Order.query.get_or_404(order_id)
        return render_template("shop/order_detail.html", order=order)


    @app.route("/orders/<int:order_id>/complete", methods=["POST"])
    def complete_order(order_id):
        order = Order.query.get_or_404(order_id)

        if order.status == "completed":
            flash("تم تنفيذ هذا الطلب مسبقًا", "warning")
            return redirect(url_for("orders"))
        
        if order.invoice_id:
            flash("هذا الطلب مرتبط بالفعل بفاتورة", "warning")
            return redirect(url_for("orders"))

        # التحقق من المخزون أولًا
        for order_item in order.items:
            product = order_item.product
            item = product.item

            if item.quantity < order_item.quantity:
                flash(f"الكمية غير كافية للمنتج: {item.name}", "danger")
                return redirect(url_for("order_detail", order_id=order.id))

        # إنشاء الفاتورة
        invoice = SalesInvoice(
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
            payment_method="طلب من الموقع",
            amount_paid=0,
            total_amount=order.total_amount
        )
        db.session.add(invoice)
        db.session.flush()

        order.invoice_id = invoice.id

        # إنشاء بنود الفاتورة + خصم المخزون + حركة المخزون
        for order_item in order.items:
            product = order_item.product
            item = product.item

            invoice_item = SalesInvoiceItem(
                invoice_id=invoice.id,
                item_id=item.id,
                quantity=order_item.quantity,
                sale_price=order_item.price,
                line_total=order_item.quantity * order_item.price
            )
            db.session.add(invoice_item)

            # خصم من المخزون
            item.quantity -= order_item.quantity

            # تسجيل حركة المخزون
            movement = StockMovement(
                item_id=item.id,
                movement_type="out",
                quantity=order_item.quantity,
                note=f"تنفيذ طلب موقع رقم #{order.id}"
            )
            db.session.add(movement)

        # تحديث حالة الطلب
        order.status = "completed"

        db.session.commit()

        flash("تم تنفيذ الطلب وإنشاء فاتورة البيع بنجاح", "success")
        return redirect(url_for("orders"))

    @app.route("/orders/<int:order_id>/invoice")
    def order_invoice(order_id):
        order = Order.query.get_or_404(order_id)

        if not order.invoice_id:
            flash("لا توجد فاتورة مرتبطة بهذا الطلب", "warning")
            return redirect(url_for("orders"))

        return redirect(url_for("edit_invoice", invoice_id=order.invoice_id))

    @app.route("/analytics")
    @login_required
    @role_required("owner")
    def analytics():
        if getattr(current_user, "role", "") != "owner":
            flash("ليس لديك صلاحية الوصول لهذه الصفحة", "danger")
            return redirect(url_for("dashboard"))

        date_from = request.args.get("date_from", "").strip()
        date_to = request.args.get("date_to", "").strip()
        warehouse_id = request.args.get("warehouse_id", "").strip()
        category_filter = request.args.get("category", "").strip()
        export = request.args.get("export", "").strip()

        invoice_query = db.session.query(SalesInvoice)
        order_query = db.session.query(Order)
        sales_items_query = db.session.query(SalesInvoiceItem).join(Item, Item.id == SalesInvoiceItem.item_id)

        if date_from:
            start_date = datetime.strptime(date_from, "%Y-%m-%d")
            invoice_query = invoice_query.filter(SalesInvoice.created_at >= start_date)
            order_query = order_query.filter(Order.created_at >= start_date)
            sales_items_query = sales_items_query.join(
                SalesInvoice, SalesInvoice.id == SalesInvoiceItem.invoice_id
            ).filter(SalesInvoice.created_at >= start_date)

        if date_to:
            end_date = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            invoice_query = invoice_query.filter(SalesInvoice.created_at < end_date)
            order_query = order_query.filter(Order.created_at < end_date)
            sales_items_query = sales_items_query.join(
                SalesInvoice, SalesInvoice.id == SalesInvoiceItem.invoice_id
            ).filter(SalesInvoice.created_at < end_date)

        if warehouse_id:
            sales_items_query = sales_items_query.filter(Item.warehouse_id == int(warehouse_id))

        if category_filter:
            sales_items_query = sales_items_query.join(
                Warehouse, Warehouse.id == Item.warehouse_id
            ).filter(Warehouse.category == category_filter)

        invoices = invoice_query.all()
        orders = order_query.all()

        total_sales = sum(inv.total_amount or 0 for inv in invoices)
        total_invoices = len(invoices)
        total_orders = len(orders)
        total_items = Item.query.count()
        low_stock_count = Item.query.filter(Item.quantity <= Item.reorder_level).count()
        average_invoice = round(total_sales / total_invoices, 2) if total_invoices else 0

        filtered_sales_items = sales_items_query.all()

        total_profit = sum(
            ((line.sale_price or 0) - (line.item.purchase_price or 0)) * (line.quantity or 0)
            for line in filtered_sales_items
        )

        # أفضل المنتجات
        top_products_map = {}
        for line in filtered_sales_items:
            name = line.item.name
            top_products_map[name] = top_products_map.get(name, 0) + (line.quantity or 0)

        top_products = sorted(
            [{"name": k, "qty": v} for k, v in top_products_map.items()],
            key=lambda x: x["qty"],
            reverse=True
        )[:5]

        # أفضل العملاء
        top_customers_raw = (
            db.session.query(
                SalesInvoice.customer_name,
                func.sum(SalesInvoice.total_amount).label("total_spent"),
                func.count(SalesInvoice.id).label("invoice_count")
            )
            .group_by(SalesInvoice.customer_name)
            .order_by(desc("total_spent"))
            .limit(5)
            .all()
        )

        top_customers = [
            {"name": row[0], "spent": row[1], "count": row[2]}
            for row in top_customers_raw
        ]

        # المنتجات الراكدة
        stagnant_products_raw = (
            db.session.query(Item.name, Item.quantity)
            .outerjoin(SalesInvoiceItem, SalesInvoiceItem.item_id == Item.id)
            .group_by(Item.id, Item.name, Item.quantity)
            .having(func.count(SalesInvoiceItem.id) == 0)
            .limit(5)
            .all()
        )

        stagnant_products = [{"name": row[0], "qty": row[1]} for row in stagnant_products_raw]

        recent_invoices = SalesInvoice.query.order_by(SalesInvoice.id.desc()).limit(5).all()
        recent_orders = Order.query.order_by(Order.id.desc()).limit(5).all()

        # آخر 7 أيام
        last_7_days = []
        sales_7_days = []
        profit_7_days = []

        for i in range(6, -1, -1):
            day = datetime.utcnow().date() - timedelta(days=i)
            next_day = day + timedelta(days=1)

            day_total = (
                db.session.query(func.sum(SalesInvoice.total_amount))
                .filter(SalesInvoice.created_at >= day)
                .filter(SalesInvoice.created_at < next_day)
                .scalar()
                or 0
            )

            day_profit_raw = (
                db.session.query(SalesInvoiceItem)
                .join(Item, Item.id == SalesInvoiceItem.item_id)
                .join(SalesInvoice, SalesInvoice.id == SalesInvoiceItem.invoice_id)
                .filter(SalesInvoice.created_at >= day)
                .filter(SalesInvoice.created_at < next_day)
                .all()
            )

            day_profit = sum(
                ((line.sale_price or 0) - (line.item.purchase_price or 0)) * (line.quantity or 0)
                for line in day_profit_raw
            )

            last_7_days.append(day.strftime("%m-%d"))
            sales_7_days.append(float(day_total))
            profit_7_days.append(float(day_profit))

        # تحليل شهري آخر 6 شهور
        monthly_labels = []
        monthly_sales = []

        current_month = datetime.utcnow().replace(day=1)
        month_points = []
        temp = current_month
        for _ in range(6):
            month_points.append(temp)
            if temp.month == 1:
                temp = temp.replace(year=temp.year - 1, month=12, day=1)
            else:
                temp = temp.replace(month=temp.month - 1, day=1)
        month_points.reverse()

        for month_start in month_points:
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1, day=1)

            month_total = (
                db.session.query(func.sum(SalesInvoice.total_amount))
                .filter(SalesInvoice.created_at >= month_start)
                .filter(SalesInvoice.created_at < month_end)
                .scalar()
                or 0
            )

            monthly_labels.append(month_start.strftime("%Y-%m"))
            monthly_sales.append(float(month_total))

        # Forecast بسيط للشهر القادم = متوسط آخر 3 شهور
        forecast_next_month = 0
        if len(monthly_sales) >= 3:
            forecast_next_month = round(sum(monthly_sales[-3:]) / 3, 2)
        elif monthly_sales:
            forecast_next_month = round(sum(monthly_sales) / len(monthly_sales), 2)

        # المقارنة الأسبوعية
        today = datetime.utcnow().date()
        start_this_week = today - timedelta(days=today.weekday())
        start_last_week = start_this_week - timedelta(days=7)

        this_week_sales = (
            db.session.query(func.sum(SalesInvoice.total_amount))
            .filter(SalesInvoice.created_at >= start_this_week)
            .scalar()
            or 0
        )

        last_week_sales = (
            db.session.query(func.sum(SalesInvoice.total_amount))
            .filter(SalesInvoice.created_at >= start_last_week)
            .filter(SalesInvoice.created_at < start_this_week)
            .scalar()
            or 0
        )

        sales_growth = 0
        if last_week_sales > 0:
            sales_growth = round(((this_week_sales - last_week_sales) / last_week_sales) * 100, 2)

        # الأسبوع الحالي مقابل السابق - عدد الطلبات
        this_week_orders = (
            db.session.query(func.count(Order.id))
            .filter(Order.created_at >= start_this_week)
            .scalar()
            or 0
        )

        last_week_orders = (
            db.session.query(func.count(Order.id))
            .filter(Order.created_at >= start_last_week)
            .filter(Order.created_at < start_this_week)
            .scalar()
            or 0
        )

        orders_growth = 0
        if last_week_orders > 0:
            orders_growth = round(((this_week_orders - last_week_orders) / last_week_orders) * 100, 2)

        # تحليل حسب الأقسام
        category_sales_raw = (
            db.session.query(
                Warehouse.category,
                func.sum(SalesInvoiceItem.line_total).label("total_sales"),
                func.sum(
                    (SalesInvoiceItem.sale_price - Item.purchase_price) * SalesInvoiceItem.quantity
                ).label("profit_total")
            )
            .join(Item, Item.id == SalesInvoiceItem.item_id)
            .join(Warehouse, Warehouse.id == Item.warehouse_id)
            .group_by(Warehouse.category)
            .order_by(desc("total_sales"))
            .all()
        )

        category_sales = []
        for row in category_sales_raw:
            sales_value = float(row[1] or 0)
            profit_value = float(row[2] or 0)
            margin = round((profit_value / sales_value) * 100, 2) if sales_value else 0
            category_sales.append({
                "name": row[0] or "غير محدد",
                "total": sales_value,
                "profit": profit_value,
                "margin": margin
            })

        # تحليل حسب المخازن
        warehouse_sales_raw = (
            db.session.query(
                Warehouse.name,
                func.sum(SalesInvoiceItem.line_total).label("total_sales")
            )
            .join(Item, Item.warehouse_id == Warehouse.id)
            .join(SalesInvoiceItem, SalesInvoiceItem.item_id == Item.id)
            .group_by(Warehouse.id, Warehouse.name)
            .order_by(desc("total_sales"))
            .limit(5)
            .all()
        )

        warehouse_sales = [
            {"name": row[0], "total": float(row[1] or 0)}
            for row in warehouse_sales_raw
        ]

        # أفضل يوم بيع
        best_day_raw = (
            db.session.query(
                func.date(SalesInvoice.created_at),
                func.sum(SalesInvoice.total_amount).label("day_total")
            )
            .group_by(func.date(SalesInvoice.created_at))
            .order_by(desc("day_total"))
            .first()
        )

        best_day = None
        if best_day_raw:
            best_day = {
                "date": str(best_day_raw[0]),
                "total": float(best_day_raw[1] or 0)
            }

        # تنبيهات إعادة الطلب
        reorder_suggestions_raw = (
            Item.query
            .filter(Item.quantity <= Item.reorder_level)
            .order_by(Item.quantity.asc())
            .limit(5)
            .all()
        )

        reorder_suggestions = [
            {
                "name": item.name,
                "qty": item.quantity,
                "reorder_level": item.reorder_level
            }
            for item in reorder_suggestions_raw
        ]

        alerts = []
        if low_stock_count > 0:
            alerts.append(f"يوجد {low_stock_count} صنف منخفض المخزون")
        if stagnant_products:
            alerts.append(f"يوجد {len(stagnant_products)} منتجات راكدة تحتاج مراجعة")
        if sales_growth < 0:
            alerts.append(f"المبيعات أقل من الأسبوع السابق بنسبة {abs(sales_growth)}%")
        if forecast_next_month > 0:
            alerts.append(f"توقع مبيعات الشهر القادم: {forecast_next_month} جنيه")

        if export == "csv":
            si = StringIO()
            writer = csv.writer(si)
            writer.writerow(["المؤشر", "القيمة"])
            writer.writerow(["إجمالي المبيعات", total_sales])
            writer.writerow(["صافي الربح", round(total_profit, 2)])
            writer.writerow(["عدد الفواتير", total_invoices])
            writer.writerow(["عدد الطلبات", total_orders])
            writer.writerow(["متوسط الفاتورة", average_invoice])
            writer.writerow(["توقع الشهر القادم", forecast_next_month])

            writer.writerow([])
            writer.writerow(["أفضل المنتجات"])
            writer.writerow(["المنتج", "الكمية"])
            for p in top_products:
                writer.writerow([p["name"], p["qty"]])

            writer.writerow([])
            writer.writerow(["أفضل العملاء"])
            writer.writerow(["العميل", "إجمالي الشراء", "عدد الفواتير"])
            for c in top_customers:
                writer.writerow([c["name"], c["spent"], c["count"]])

            writer.writerow([])
            writer.writerow(["تحليل الأقسام"])
            writer.writerow(["القسم", "المبيعات", "الربح", "هامش الربح %"])
            for c in category_sales:
                writer.writerow([c["name"], c["total"], c["profit"], c["margin"]])

            return Response(
                si.getvalue(),
                mimetype="text/csv; charset=utf-8",
                headers={"Content-Disposition": "attachment; filename=analytics_report.csv"}
            )

        warehouses = Warehouse.query.order_by(Warehouse.name.asc()).all()
        categories = db.session.query(Warehouse.category).distinct().all()
        categories = [c[0] for c in categories if c[0]]

        return render_template(
            "analytics.html",
            total_sales=round(total_sales, 2),
            total_profit=round(total_profit, 2),
            total_invoices=total_invoices,
            total_orders=total_orders,
            total_items=total_items,
            low_stock_count=low_stock_count,
            average_invoice=average_invoice,
            forecast_next_month=forecast_next_month,
            orders_growth=orders_growth,
            top_products=top_products,
            top_customers=top_customers,
            stagnant_products=stagnant_products,
            reorder_suggestions=reorder_suggestions,
            recent_invoices=recent_invoices,
            recent_orders=recent_orders,
            last_7_days=last_7_days,
            sales_7_days=sales_7_days,
            profit_7_days=profit_7_days,
            monthly_labels=monthly_labels,
            monthly_sales=monthly_sales,
            date_from=date_from,
            date_to=date_to,
            warehouse_id=warehouse_id,
            category_filter=category_filter,
            warehouses=warehouses,
            categories=categories,
            this_week_sales=round(this_week_sales, 2),
            last_week_sales=round(last_week_sales, 2),
            sales_growth=sales_growth,
            category_sales=category_sales,
            warehouse_sales=warehouse_sales,
            best_day=best_day,
            alerts=alerts
        )

    @app.route("/reports")
    @login_required
    @role_required("owner")
    def reports():
        if getattr(current_user, "role", "") != "owner":
            flash("ليس لديك صلاحية الوصول لهذه الصفحة", "danger")
            return redirect(url_for("dashboard"))

        date_from = request.args.get("date_from", "").strip()
        date_to = request.args.get("date_to", "").strip()

        invoice_query = SalesInvoice.query
        sales_items_query = (
            db.session.query(SalesInvoiceItem)
            .join(Item, Item.id == SalesInvoiceItem.item_id)
            .join(SalesInvoice, SalesInvoice.id == SalesInvoiceItem.invoice_id)
        )
        if date_from:
            start_date = datetime.strptime(date_from, "%Y-%m-%d")
            invoice_query = invoice_query.filter(SalesInvoice.created_at >= start_date)
            sales_items_query = sales_items_query.filter(SalesInvoice.created_at >= start_date)

        if date_to:
            end_date = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            invoice_query = invoice_query.filter(SalesInvoice.created_at < end_date)
            sales_items_query = sales_items_query.filter(SalesInvoice.created_at < end_date)

        invoices = invoice_query.order_by(SalesInvoice.created_at.desc()).all()
        sales_items = sales_items_query.all()

        total_sales = sum(inv.total_amount or 0 for inv in invoices)
        total_profit = sum(
            ((line.sale_price or 0) - (line.item.purchase_price or 0)) * (line.quantity or 0)
            for line in sales_items
        )
        total_invoices = len(invoices)
        average_invoice = round(total_sales / total_invoices, 2) if total_invoices else 0

        report_rows = []
        for inv in invoices:
            report_rows.append({
                "invoice_id": inv.id,
                "customer_name": inv.customer_name,
                "date": inv.created_at.strftime("%Y-%m-%d %H:%M"),
                "total": inv.total_amount or 0,
                "paid": inv.amount_paid or 0,
                "balance": inv.balance_due if hasattr(inv, "balance_due") else ((inv.total_amount or 0) - (inv.amount_paid or 0)),
            })

        return render_template(
            "reports.html",
            date_from=date_from,
            date_to=date_to,
            total_sales=round(total_sales, 2),
            total_profit=round(total_profit, 2),
            total_invoices=total_invoices,
            average_invoice=average_invoice,
            report_rows=report_rows
        )


    @app.route("/reports/export")
    @login_required
    def export_reports_csv():
        if getattr(current_user, "role", "") != "owner":
            flash("ليس لديك صلاحية الوصول لهذه الصفحة", "danger")
            return redirect(url_for("dashboard"))

        date_from = request.args.get("date_from", "").strip()
        date_to = request.args.get("date_to", "").strip()

        invoice_query = SalesInvoice.query

        if date_from:
            start_date = datetime.strptime(date_from, "%Y-%m-%d")
            invoice_query = invoice_query.filter(SalesInvoice.created_at >= start_date)

        if date_to:
            end_date = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            invoice_query = invoice_query.filter(SalesInvoice.created_at < end_date)

        invoices = invoice_query.order_by(SalesInvoice.created_at.desc()).all()

        si = StringIO()
        writer = csv.writer(si)

        writer.writerow(["رقم الفاتورة", "العميل", "التاريخ", "الإجمالي", "المدفوع", "المتبقي"])

        for inv in invoices:
            writer.writerow([
                inv.id,
                inv.customer_name,
                inv.created_at.strftime("%Y-%m-%d %H:%M"),
                inv.total_amount or 0,
                inv.amount_paid or 0,
                inv.balance_due if hasattr(inv, "balance_due") else ((inv.total_amount or 0) - (inv.amount_paid or 0)),
            ])

        return Response(
            si.getvalue(),
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=sales_report.csv"}
        )


    @app.route("/reports/print")
    @login_required
    def print_reports():
        if getattr(current_user, "role", "") != "owner":
            flash("ليس لديك صلاحية الوصول لهذه الصفحة", "danger")
            return redirect(url_for("dashboard"))

        date_from = request.args.get("date_from", "").strip()
        date_to = request.args.get("date_to", "").strip()

        invoice_query = SalesInvoice.query
        sales_items_query = (
            db.session.query(SalesInvoiceItem)
            .join(Item, Item.id == SalesInvoiceItem.item_id)
            .join(SalesInvoice, SalesInvoice.id == SalesInvoiceItem.invoice_id)
        )

        if date_from:
            start_date = datetime.strptime(date_from, "%Y-%m-%d")
            invoice_query = invoice_query.filter(SalesInvoice.created_at >= start_date)
            sales_items_query = sales_items_query.filter(SalesInvoice.created_at >= start_date)

        if date_to:
            end_date = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            invoice_query = invoice_query.filter(SalesInvoice.created_at < end_date)
            sales_items_query = sales_items_query.filter(SalesInvoice.created_at < end_date)

        invoices = invoice_query.order_by(SalesInvoice.created_at.desc()).all()
        sales_items = sales_items_query.all()
        total_sales = sum(inv.total_amount or 0 for inv in invoices)
        total_profit = sum(
            ((line.sale_price or 0) - (line.item.purchase_price or 0)) * (line.quantity or 0)
            for line in sales_items
        )
        total_invoices = len(invoices)
        average_invoice = round(total_sales / total_invoices, 2) if total_invoices else 0

        return render_template(
            "reports_print.html",
            date_from=date_from,
            date_to=date_to,
            invoices=invoices,
            total_sales=round(total_sales, 2),
            total_profit=round(total_profit, 2),
            total_invoices=total_invoices,
            average_invoice=average_invoice
        )


    @app.route("/alerts")
    @login_required
    @role_required("owner")
    def alerts_page():
        if getattr(current_user, "role", "") != "owner":
            flash("ليس لديك صلاحية الوصول لهذه الصفحة", "danger")
            return redirect(url_for("dashboard"))

        low_stock_items = Item.query.filter(Item.quantity <= Item.reorder_level).order_by(Item.quantity.asc()).all()

        stagnant_products_raw = (
            db.session.query(Item)
            .outerjoin(SalesInvoiceItem, SalesInvoiceItem.item_id == Item.id)
            .group_by(Item.id)
            .having(func.count(SalesInvoiceItem.id) == 0)
            .all()
        )

        alerts = {
            "low_stock": low_stock_items,
            "stagnant": stagnant_products_raw
        }

        return render_template("alerts.html", alerts=alerts)

    def get_system_alerts():
        low_stock_items = Item.query.filter(Item.quantity <= Item.reorder_level).all()

        stagnant_products = (
            db.session.query(Item)
            .outerjoin(SalesInvoiceItem, SalesInvoiceItem.item_id == Item.id)
            .group_by(Item.id)
            .having(func.count(SalesInvoiceItem.id) == 0)
            .all()
        )

        pending_orders = Order.query.filter_by(status="pending").count()

        alerts = {
            "low_stock_count": len(low_stock_items),
            "stagnant_count": len(stagnant_products),
            "pending_orders_count": pending_orders,
            "total_alerts": len(low_stock_items) + len(stagnant_products) + pending_orders
        }
        return alerts

    @app.route("/owner-kpi")
    @login_required
    @role_required("owner")
    def owner_kpi():
        total_sales = db.session.query(func.sum(SalesInvoice.total_amount)).scalar() or 0
        total_orders = Order.query.count()
        total_invoices = SalesInvoice.query.count()
        low_stock_count = Item.query.filter(Item.quantity <= Item.reorder_level).count()

        best_customer = (
            db.session.query(
                SalesInvoice.customer_name,
                func.sum(SalesInvoice.total_amount).label("spent")
            )
            .group_by(SalesInvoice.customer_name)
            .order_by(desc("spent"))
            .first()
        )

        best_product = (
            db.session.query(
                Item.name,
                func.sum(SalesInvoiceItem.quantity).label("qty")
            )
            .join(SalesInvoiceItem, SalesInvoiceItem.item_id == Item.id)
            .group_by(Item.name)
            .order_by(desc("qty"))
            .first()
        )

        return render_template(
            "owner_kpi.html",
            total_sales=round(total_sales, 2),
            total_orders=total_orders,
            total_invoices=total_invoices,
            low_stock_count=low_stock_count,
            best_customer=best_customer,
            best_product=best_product,
        )

    def get_order_status_step(status):
        mapping = {
            "pending": 1,
            "confirmed": 2,
            "shipping": 3,
            "completed": 4
        }
        return mapping.get(status, 1)


    @app.route("/order-success/<order_number>")
    def order_success(order_number):
        order = Order.query.filter_by(order_number=order_number).first_or_404()
        return render_template("shop/order_success.html", order=order)


    @app.route("/track-order", methods=["GET"])
    def track_order_search():
        order_number = request.args.get("order_number", "").strip()
        order = None

        if order_number:
            order = Order.query.filter_by(order_number=order_number).first()

        return render_template(
            "shop/track_order.html",
            order=order,
            searched_order_number=order_number,
            current_step=get_order_status_step(order.status) if order else 1
        )


    @app.route("/track-order/<order_number>")
    def track_order(order_number):
        order = Order.query.filter_by(order_number=order_number).first_or_404()

        return render_template(
            "shop/track_order.html",
            order=order,
            searched_order_number=order.order_number,
            current_step=get_order_status_step(order.status)
        )


    @app.route("/admin/orders", methods=["GET"])
    @login_required
    def admin_orders():
        search = request.args.get("q", "").strip()
        status_filter = request.args.get("status", "").strip()

        query = Order.query

        if search:
            query = query.filter(
                or_(
                    Order.order_number.ilike(f"%{search}%"),
                    Order.customer_name.ilike(f"%{search}%")
                )
            )

        if status_filter:
            query = query.filter(Order.status == status_filter)

        orders = query.order_by(Order.created_at.desc()).all()

        return render_template(
            "shop/admin_orders.html",
            orders=orders,
            search=search,
            status_filter=status_filter
        )


    @app.route("/admin/orders/<int:order_id>")
    @login_required
    def admin_order_detail(order_id):
        order = Order.query.get_or_404(order_id)
        return render_template("shop/order_detail.html", order=order)

    def generate_order_number():
        import uuid
        today = datetime.utcnow().strftime("%Y%m%d")
        random_part = str(uuid.uuid4()).replace("-", "").upper()[:8]
        return f"BDY-{today}-{random_part}"