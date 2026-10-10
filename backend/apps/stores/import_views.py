from io import BytesIO
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from openpyxl import Workbook
from rest_framework import serializers
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .imports import validate_import
from .models import Product, Store
from .serializers import ProductSerializer


class ProductImportWriteError(Exception):
    def __init__(self, row):
        self.row = row


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def import_products(request, slug):
    # Resolve the slug only through a writable membership for the authenticated user.
    store = Store.objects.filter(
        slug=slug,
        memberships__user=request.user,
        memberships__role__in=['owner', 'admin', 'editor'],
    ).distinct().first()
    if not store:
        return Response({'detail': 'Store not found or access denied.'}, status=404)

    upload = request.FILES.get('file')
    if not upload:
        return Response({'file': 'Upload a CSV or XLSX file.'}, status=400)
    try:
        valid, errors, preview = validate_import(upload, store)
    except serializers.ValidationError as exc:
        return Response({'detail': exc.detail}, status=400)
    except Exception:
        return Response({'detail': 'Could not validate the uploaded file.'}, status=400)

    commit = str(request.data.get('commit', 'false')).lower() in ('true', '1', 'yes')
    created = []
    if commit and valid:
        try:
            # Treat the accepted rows as one unit. A write/constraint failure rolls
            # every product from this confirmation back, leaving the store unchanged.
            with transaction.atomic():
                for row_number, values in enumerate(valid, start=2):
                    try:
                        serializer = ProductSerializer(data=values, context={'store': store})
                        serializer.is_valid(raise_exception=True)
                        created.append(serializer.save(store=store))
                    except (IntegrityError, serializers.ValidationError) as exc:
                        raise ProductImportWriteError(row_number) from exc
        except ProductImportWriteError as exc:
            return Response({
                'detail': 'No products were imported because a row failed during database save.',
                'successful_rows': 0,
                'errors': [{'row': exc.row, 'sku': valid[exc.row - 2].get('sku'), 'errors': ['A duplicate or invalid product prevented saving this row.']}],
            }, status=409)

    return Response({
        'preview_only': not commit,
        'total_validated': len(valid) + len(errors),
        'successful_rows': len(created),
        'valid_rows': len(valid),
        'failed_rows': len(errors),
        'errors': errors,
        'preview': preview,
        'products': ProductSerializer(created, many=True, context={'store': store}).data if commit else [],
    }, status=200 if not errors else 207)


@api_view(['GET'])
def product_import_template(request, slug):
    store = Store.objects.filter(
        slug=slug,
        memberships__user=request.user,
        memberships__role__in=['owner', 'admin', 'editor'],
    ).distinct().first()
    if not store:
        return Response({'detail': 'Store not found or access denied.'}, status=404)

    category = store.categories.order_by('name').values_list('name', flat=True).first() or 'REPLACE_WITH_EXISTING_CATEGORY'
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Products'
    sheet.append(['name', 'price', 'stock', 'category', 'sku', 'description', 'image_url'])
    sheet.append(['Sample Green Tea', 199.00, 10, category, '', 'Loose leaf green tea', ''])
    sheet.append(['Sample Herbal Tea', 149.00, 8, category, '', 'Caffeine-free herbal blend', ''])
    sheet.freeze_panes = 'A2'
    sheet.auto_filter.ref = sheet.dimensions
    for column, width in {'A': 28, 'B': 12, 'C': 12, 'D': 24, 'E': 18, 'F': 34, 'G': 40}.items():
        sheet.column_dimensions[column].width = width
    output = BytesIO()
    workbook.save(output)
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="smartstore-products-template.xlsx"'
    return response
