from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, IntegerField, FloatField
from wtforms.validators import DataRequired, Email

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class WarehouseForm(FlaskForm):
    name = StringField("Warehouse Name", validators=[DataRequired()])
    category = SelectField(
        "Category",
        choices=[
            ("المكتبة", "المكتبة"),
            ("الأعلاف", "الأعلاف"),
            ("المزرعة", "المزرعة"),
            ("المصروفات", "المصروفات"),
            ("أخرى", "أخرى"),
        ],
        validators=[DataRequired()]
    )
    notes = TextAreaField("Notes")
    submit = SubmitField("حفظ")

class ItemForm(FlaskForm):
    item_code = StringField("Item Code", validators=[DataRequired()])
    name = StringField("Item Name", validators=[DataRequired()])
    description = TextAreaField("Description")
    purchase_price = FloatField("Purchase Price", validators=[DataRequired()])
    sale_price = FloatField("Sale Price", validators=[DataRequired()])
    quantity = IntegerField("Quantity", validators=[DataRequired()])
    reorder_level = IntegerField("Reorder Level", validators=[DataRequired()])
    warehouse_id = SelectField("Warehouse", coerce=int, validators=[DataRequired()])
    notes = TextAreaField("Notes")
    submit = SubmitField("حفظ")

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange


class SalesInvoiceForm(FlaskForm):
    customer_name = StringField("اسم العميل", validators=[DataRequired()])
    customer_phone = StringField("رقم الهاتف", validators=[Optional()])
    notes = TextAreaField("ملاحظات", validators=[Optional()])
    submit = SubmitField("حفظ الفاتورة")


class SalesInvoiceItemForm(FlaskForm):
    item_id = SelectField("الصنف", coerce=int, validators=[DataRequired()])
    quantity = IntegerField("الكمية", validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField("إضافة الصنف")

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, FloatField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange


class SalesInvoiceForm(FlaskForm):
    customer_name = StringField("اسم العميل", validators=[DataRequired()])
    customer_phone = StringField("رقم الهاتف", validators=[Optional()])
    notes = TextAreaField("ملاحظات", validators=[Optional()])
    payment_method = SelectField(
        "طريقة الدفع",
        choices=[
            ("cash", "نقدي"),
            ("transfer", "تحويل"),
            ("deferred", "آجل"),
        ],
        validators=[DataRequired()]
    )
    amount_paid = FloatField("المبلغ المدفوع", validators=[Optional()], default=0)
    submit = SubmitField("إنشاء الفاتورة")


class SalesInvoiceItemForm(FlaskForm):
    item_id = SelectField("الصنف", coerce=int, validators=[DataRequired()])
    quantity = IntegerField("الكمية", validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField("إضافة الصنف")