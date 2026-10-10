from rest_framework import serializers

from .models import Order, OrderItem, OrderStatusHistory


class OrderItemReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'name', 'quantity', 'unit_price')


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ('id', 'from_status', 'to_status', 'changed_by', 'created_at', 'note')


class OrderReadSerializer(serializers.ModelSerializer):
    items = OrderItemReadSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)
    store_slug = serializers.CharField(source='store.slug', read_only=True)

    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'store', 'store_name', 'store_slug', 'customer', 'customer_name',
            'customer_phone', 'delivery_address', 'status', 'payment_method',
            'payment_status', 'currency', 'subtotal', 'delivery_charge',
            'total', 'items', 'status_history', 'created_at', 'updated_at',
        )
