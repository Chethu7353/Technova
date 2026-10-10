import csv
import io
from decimal import Decimal, InvalidOperation

from openpyxl import load_workbook
from rest_framework.exceptions import ValidationError

from .models import Category
from .serializers import ProductSerializer

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
REQUIRED_HEADERS = {'name', 'price', 'stock', 'category'}
OPTIONAL_HEADERS = {'sku', 'description', 'image_url'}


def read_rows(upload):
    if upload.size > MAX_UPLOAD_BYTES:
        raise ValidationError({'file': 'File must be 10 MB or smaller.'})
    name = upload.name.lower()
    if name.endswith('.csv'):
        try:
            return list(csv.reader(io.StringIO(upload.read().decode('utf-8-sig'))))
        except (UnicodeDecodeError, csv.Error):
            raise ValidationError({'file': 'CSV must be valid UTF-8.'})
    if name.endswith('.xlsx'):
        try:
            workbook = load_workbook(upload, read_only=True, data_only=True, keep_links=False)
            try:
                return [list(row) for row in workbook.active.iter_rows(values_only=True)]
            finally:
                workbook.close()
        except Exception:
            raise ValidationError({'file': 'Could not read this XLSX workbook.'})
    raise ValidationError({'file': 'Only CSV and XLSX files are supported. XLSM is not accepted.'})


def validate_import(upload, store):
    rows = read_rows(upload)
    if not rows or not any(str(value or '').strip() for value in rows[0]):
        return [], [{'row': 1, 'sku': '', 'errors': ['CSV file is empty; include the required header row.']}], []

    headers = [str(value or '').strip().lower().replace(' ', '_') for value in rows[0]]
    header_issues = []
    missing = REQUIRED_HEADERS - set(headers)
    if missing:
        header_issues.append(f'Missing required columns: {", ".join(sorted(missing))}.')
    if len(headers) != len(set(headers)):
        header_issues.append('Column headers must be unique.')
    unsupported = set(headers) - REQUIRED_HEADERS - OPTIONAL_HEADERS
    if unsupported:
        header_issues.append(f'Unsupported columns: {", ".join(sorted(unsupported))}.')
    if header_issues:
        return [], [{'row': 1, 'sku': '', 'errors': header_issues}], []

    indexes = {header: index for index, header in enumerate(headers)}
    if not any(any(value not in (None, '') for value in row) for row in rows[1:]):
        return [], [{'row': 1, 'sku': '', 'errors': ['No product data rows were found below the header.']}], []
    valid, errors, preview = [], [], []
    categories = {category.name.casefold(): category for category in Category.objects.filter(store=store)}
    existing_skus = {sku.casefold() for sku in store.products.exclude(sku__isnull=True).exclude(sku='').values_list('sku', flat=True)}
    seen_skus = set()

    for row_number, row in enumerate(rows[1:], start=2):
        if not any(value not in (None, '') for value in row):
            continue
        raw = {header: (row[index] if index < len(row) else None) for header, index in indexes.items()}
        name = str(raw.get('name') or '').strip()
        sku = str(raw.get('sku') or '').strip()
        issues = []
        if not name or len(name) > 180:
            issues.append('name is required and must be 180 characters or fewer')
        try:
            price = Decimal(str(raw.get('price') if raw.get('price') is not None else '').strip())
            if not price.is_finite() or price <= 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            price = None
            issues.append('price must be a positive numeric value')
        try:
            stock_value = Decimal(str(raw.get('stock') if raw.get('stock') is not None else '').strip())
            if not stock_value.is_finite() or stock_value < 0 or stock_value != stock_value.to_integral_value():
                raise InvalidOperation
            stock = int(stock_value)
        except (InvalidOperation, ValueError):
            stock = None
            issues.append('stock must be a non-negative whole number')
        if sku and (sku.casefold() in existing_skus or sku.casefold() in seen_skus):
            issues.append('SKU already exists in this store or this file')

        category_name = str(raw.get('category') or '').strip()
        category = categories.get(category_name.casefold()) if category_name else None
        if not category:
            issues.append(f'category "{category_name}" is required and must match an existing category in this store')

        image_url = str(raw.get('image_url') or '').strip()
        item = {
            'name': name,
            'sku': sku or None,
            'description': str(raw.get('description') or '')[:5000],
            'price': price,
            'stock': stock,
            'category': category.pk if category else None,
            'image_url': image_url,
        }
        if not issues:
            serializer = ProductSerializer(data=item, context={'store': store})
            if not serializer.is_valid():
                issues.extend(f'{field}: {", ".join(messages)}' for field, messages in serializer.errors.items())
        if issues:
            errors.append({'row': row_number, 'sku': sku, 'errors': issues})
            continue
        if sku:
            seen_skus.add(sku.casefold())
        valid.append(item)
        if len(preview) < 20:
            preview.append({**item, 'price': str(price), 'category_name': category.name})
    return valid, errors, preview
