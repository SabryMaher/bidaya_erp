import csv
from pathlib import Path

from app import db
from app.models import Item, Warehouse


def clean_text(value):
    if value is None:
        return ""
    return (
        str(value)
        .replace("\ufeff", "")
        .replace("\xa0", " ")
        .strip()
    )


def clean_number(value):
    if not value:
        return 0.0

    value = str(value)

    # إزالة النصوص
    value = value.replace("جنيه", "")
    value = value.replace("EGP", "")
    value = value.replace(",", "")
    value = value.replace("٫", ".")
    value = value.replace(" ", "")

    # احتفظ بالأرقام فقط
    cleaned = ""
    for ch in value:
        if ch.isdigit() or ch == ".":
            cleaned += ch

    try:
        return float(cleaned)
    except:
        return 0.0


def normalize_header(text):
    return (
        clean_text(text)
        .lower()
        .replace("_", " ")
    )


def find_column_index(headers, candidates):
    normalized = [normalize_header(h) for h in headers]

    # exact/contains matching
    for candidate in candidates:
        c = normalize_header(candidate)
        for idx, header in enumerate(normalized):
            if c == header or c in header or header in c:
                return idx

    return None


def import_from_csv(file_path):
    path = Path(file_path)
    if not path.exists():
        raise Exception(f"ملف البيانات غير موجود: {file_path}")

    encodings = ["utf-8-sig", "utf-8", "cp1256", "windows-1256"]
    raw_text = None

    for enc in encodings:
        try:
            raw_text = path.read_text(encoding=enc)
            break
        except UnicodeDecodeError:
            continue

    if raw_text is None:
        raise Exception("تعذر قراءة الملف، الترميز غير مدعوم")

    if not raw_text.strip():
        raise Exception("الملف فارغ")

    # detect delimiter
    sample = raw_text[:5000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        delimiter = dialect.delimiter
    except Exception:
        delimiter = ","

    rows = list(csv.reader(raw_text.splitlines(), delimiter=delimiter))

    if not rows or len(rows) < 2:
        raise Exception("الملف لا يحتوي على صفوف كافية")

    headers = [clean_text(h) for h in rows[0]]
    data_rows = rows[1:]

    # محاولة العثور على الأعمدة
    idx_item_code = find_column_index(headers, ["Item ID", "item id", "id"])
    idx_name = find_column_index(headers, ["الوصف", "description", "name", "item name"])
    idx_purchase = find_column_index(headers, ["سعر شراء الوحدة", "purchase price", "buy price"])
    idx_sale = find_column_index(headers, ["سعر بيع الوحدة", "sale price", "sell price"])
    idx_profit = find_column_index(headers, ["مكسب الوحدة", "profit", "unit profit"])
    idx_warehouse = find_column_index(headers, ["نوع المخزن", "warehouse", "warehouse type", "store type"])

    # fallback حسب ترتيب الملف المتوقع من صورتك
    # [Item ID, الوصف, سعر شراء الوحدة, سعر بيع الوحدة, مكسب الوحدة, نوع المخزن]
    if idx_item_code is None and len(headers) >= 1:
        idx_item_code = 0
    if idx_name is None and len(headers) >= 2:
        idx_name = 1
    if idx_purchase is None and len(headers) >= 3:
        idx_purchase = 2
    if idx_sale is None and len(headers) >= 4:
        idx_sale = 3
    if idx_profit is None and len(headers) >= 5:
        idx_profit = 4
    if idx_warehouse is None and len(headers) >= 6:
        idx_warehouse = 5

    if idx_item_code is None or idx_name is None:
        raise Exception(f"تعذر تحديد الأعمدة. الأعمدة الموجودة: {headers}")

    imported_count = 0
    skipped_count = 0

    for row in data_rows:
        if not row:
            continue

        # بعض الصفوف قد تكون أقصر من الهيدر
        row = list(row) + [""] * max(0, len(headers) - len(row))

        item_code = clean_text(row[idx_item_code]) if idx_item_code < len(row) else ""
        name = clean_text(row[idx_name]) if idx_name < len(row) else ""
        purchase_price = clean_number(row[idx_purchase]) if idx_purchase is not None and idx_purchase < len(row) else 0.0
        sale_price = clean_number(row[idx_sale]) if idx_sale is not None and idx_sale < len(row) else 0.0
        warehouse_name = clean_text(row[idx_warehouse]) if idx_warehouse is not None and idx_warehouse < len(row) else "افتراضي"

        if not warehouse_name:
            warehouse_name = "افتراضي"

        if not item_code or not name:
            skipped_count += 1
            continue

        warehouse = Warehouse.query.filter_by(name=warehouse_name).first()
        if not warehouse:
            warehouse = Warehouse(
                name=warehouse_name,
                category=warehouse_name,
                notes=""
            )
            db.session.add(warehouse)
            db.session.flush()

        existing_item = Item.query.filter_by(item_code=item_code).first()
        if existing_item:
            skipped_count += 1
            continue

        item = Item(
            item_code=item_code,
            name=name,
            description="",
            purchase_price=purchase_price,
            sale_price=sale_price,
            unit_profit=sale_price - purchase_price,
            quantity=0,
            reorder_level=0,
            warehouse_id=warehouse.id,
            notes=""
        )

        db.session.add(item)
        imported_count += 1

    db.session.commit()

    if imported_count == 0:
        sample_row = data_rows[0] if data_rows else []
        raise Exception(
            f"لم يتم استيراد أي أصناف. الأعمدة: {headers} | أول صف بيانات: {sample_row}"
        )

    return imported_count, skipped_count, headers