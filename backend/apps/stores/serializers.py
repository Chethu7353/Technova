
from rest_framework import serializers
from .models import Store, Category, Product


class StoreSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, allow_blank=True)

    class Meta:
        model = Store
        fields = (
            'id', 'name', 'slug', 'logo', 'banner_url', 'contact_email',
            'logo_image', 'banner_image', 'phone', 'business_info', 'theme', 'theme_settings',
            'is_published', 'created_at'
        )
        read_only_fields = ('id', 'is_published', 'created_at')

    def validate_slug(self, value):
        if value and Store.objects.filter(slug=value).exclude(pk=getattr(self.instance, 'pk', None)).exists():
            raise serializers.ValidationError('This slug is already in use.')
        return value


class StoreAssetSerializer(serializers.ModelSerializer):
    logo_image = serializers.ImageField(required=False)
    banner_image = serializers.ImageField(required=False)

    class Meta:
        model = Store
        fields = ('logo_image', 'banner_image')

    def validate_logo_image(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('Logo image must be 5 MB or smaller.')
        return value

    def validate_banner_image(self, value):
        if value.size > 8 * 1024 * 1024:
            raise serializers.ValidationError('Banner image must be 8 MB or smaller.')
        return value


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'is_demo', 'created_at')
        read_only_fields = ('id', 'is_demo', 'created_at')

    def validate_name(self, value):
        store = self.context.get('store')
        if store and Category.objects.filter(store=store, name__iexact=value.strip()).exclude(pk=getattr(self.instance, 'pk', None)).exists():
            raise serializers.ValidationError('A category with this name already exists in this store.')
        return value.strip()


class ProductSerializer(serializers.ModelSerializer):
    is_demo = serializers.BooleanField(required=False, default=False)
    sku = serializers.CharField(max_length=80, allow_blank=True, allow_null=True, required=False)
    class Meta:
        model = Product
        fields = (
            'id', 'category', 'name', 'description', 'sku',
            'price', 'stock', 'low_stock_threshold', 'image_url',
            'is_demo', 'is_active', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'created_at', 'updated_at'
        )

    def validate_category(self, value):
        store = self.context.get('store')
        if value and store and value.store_id != store.id:
            raise serializers.ValidationError(
                'Category must belong to this store.'
            )
        return value

    def validate_sku(self, value):
        if value in ('', None):
            return None
        store = self.context.get('store')
        if not store:
            return value

        queryset = Product.objects.filter(store=store, sku__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                'A product with this SKU already exists in this store.'
            )
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Price must be greater than 0.'
            )
        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError(
                'Stock cannot be negative.'
            )
        return value

    def validate_low_stock_threshold(self, value):
        if value < 0:
            raise serializers.ValidationError(
                'Low-stock threshold cannot be negative.'
            )
        return value


class PublicProductSerializer(serializers.ModelSerializer):
    """Expose only fields needed by storefront customers."""
    class Meta:
        model = Product
        fields = ('id', 'category', 'name', 'description', 'price', 'stock', 'image_url')


