
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny

from apps.stores import views
from apps.stores.import_views import import_products, product_import_template
from apps.stores.assistant_views import ai_chat
from apps.stores.models import Store
from apps.stores.order_views import (
    cancel_customer_order, checkout, checkout_config, collect_cod_payment, create_payment, customer_order_detail,
    customer_orders, fail_payment, store_orders, update_order_status,
    verify_payment,
)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'email', 'password')
        read_only_fields = ('id',)

    def create(self, data):
        return get_user_model().objects.create_user(**data)


class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


@api_view(['GET'])
@permission_classes([AllowAny])
def slug_availability(request):
    slug = request.query_params.get('slug', '').strip()
    if not slug:
        return Response({'detail': 'slug query parameter is required.'}, status=400)
    from django.utils.text import slugify
    normalized = slugify(slug)
    return Response({'slug': normalized, 'available': bool(normalized) and not Store.objects.filter(slug=normalized).exists()})

@api_view(['GET'])
def me(request):
    return Response({
        'id': request.user.id,
        'username': request.user.username,
        'email': request.user.email,
    })


router = DefaultRouter()
router.register('stores', views.StoreViewSet, basename='store')


urlpatterns = [
    path('auth/register/', RegisterView.as_view()),
    path('auth/login/', TokenObtainPairView.as_view()),
    path('auth/refresh/', TokenRefreshView.as_view()),
    path('auth/me/', me),
    path('ai/chat/', ai_chat),
    path('stores/slug-availability/', slug_availability),
    path('stores/<int:pk>/assets/', views.store_assets),
    path('orders/my/', customer_orders),
    path('orders/my/<str:order_number>/', customer_order_detail),
    path('orders/my/<str:order_number>/cancel/', cancel_customer_order),
    path('orders/<str:order_number>/payment/create/', create_payment),
    path('orders/<str:order_number>/payment/verify/', verify_payment),
    path('orders/<str:order_number>/payment/fail/', fail_payment),

    path('', include(router.urls)),

    # Categories
    path(
        'stores/<slug:slug>/categories/',
        views.categories
    ),
    path(
        'stores/<slug:slug>/categories/bulk/',
        views.bulk_categories
    ),

    # Products
    path(
        'stores/<slug:slug>/products/',
        views.products
    ),
    path(
        'stores/<slug:slug>/products/import/template/',
        product_import_template
    ),
    path(
        'stores/<slug:slug>/products/import/',
        import_products
    ),
    path(
        'stores/<slug:slug>/products/<int:pk>/',
        views.product_detail
    ),

    # Themes
    path(
        'stores/<slug:slug>/themes/',
        views.theme
    ),
    path(
        'stores/<slug:slug>/theme/',
        views.theme
    ),

    # Publishing and analytics
    path(
        'stores/<slug:slug>/publish/',
        views.publish
    ),
    path(
        'stores/<slug:slug>/analytics/',
        views.analytics
    ),

    # Public store
    path('public/stores/<slug:slug>/checkout/', checkout),
    path('public/stores/<slug:slug>/checkout/config/', checkout_config),
    path('stores/<slug:slug>/orders/', store_orders),
    path('stores/<slug:slug>/orders/<str:order_number>/status/', update_order_status),
    path('stores/<slug:slug>/orders/<str:order_number>/payment/collect/', collect_cod_payment),
    path(
        'public/stores/<slug:slug>/',
        views.public_store
    ),
    path(
        'public/stores/<slug:slug>/products/<int:pk>/',
        views.public_product
    ),
]
