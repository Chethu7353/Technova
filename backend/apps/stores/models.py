from django.conf import settings
from django.db import models
from django.utils.text import slugify
import uuid

THEMES = [(x, x.replace('-', ' ').title()) for x in ('modern-clean','premium-dark','fresh-grocery','elegant-boutique')]


def generate_order_number():
    return f'SS-{uuid.uuid4().hex[:20].upper()}'

class Store(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='owned_stores')
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=80, unique=True)
    logo = models.URLField(blank=True)
    banner_url = models.URLField(blank=True)
    logo_image = models.ImageField(upload_to='stores/logos/', blank=True, null=True)
    banner_image = models.ImageField(upload_to='stores/banners/', blank=True, null=True)
    contact_email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    business_info = models.JSONField(default=dict, blank=True)
    theme = models.CharField(max_length=32, choices=THEMES, default='modern-clean')
    theme_settings = models.JSONField(default=dict, blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:70] or 'store'; candidate = base; i = 2
            while Store.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f'{base[:74]}-{i}'; i += 1
            self.slug = candidate
        super().save(*args, **kwargs)

class Membership(models.Model):
    class Role(models.TextChoices):
        OWNER='owner','Owner'; ADMIN='admin','Admin'; EDITOR='editor','Editor'; VIEWER='viewer','Viewer'
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='store_memberships')
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.VIEWER)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['store','user'], name='unique_store_member')]

class Category(models.Model):
    store=models.ForeignKey(Store,on_delete=models.CASCADE,related_name='categories')
    name=models.CharField(max_length=100)
    is_demo=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['store','name'],name='unique_store_category')]

class Product(models.Model):
    store=models.ForeignKey(Store,on_delete=models.CASCADE,related_name='products')
    category=models.ForeignKey(Category,on_delete=models.SET_NULL,null=True,blank=True,related_name='products')
    name=models.CharField(max_length=180)
    description=models.TextField(blank=True)
    sku=models.CharField(max_length=80,blank=True,null=True)
    price=models.DecimalField(max_digits=12,decimal_places=2)
    stock=models.PositiveIntegerField(default=0)
    low_stock_threshold=models.PositiveIntegerField(default=5)
    image_url=models.URLField(blank=True)
    is_demo=models.BooleanField(default=False)
    is_active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['store','sku'],name='unique_store_sku')]
        indexes=[models.Index(fields=['store','is_active']),models.Index(fields=['store','stock'])]

class Order(models.Model):
    class Status(models.TextChoices):
        PLACED='placed','Placed'; CONFIRMED='confirmed','Confirmed'; PROCESSING='processing','Processing'; SHIPPED='shipped','Shipped'; DELIVERED='delivered','Delivered'; CANCELLED='cancelled','Cancelled'
    class PaymentMethod(models.TextChoices):
        COD='cod','Cash on delivery'; RAZORPAY='razorpay','Razorpay'; LEGACY='legacy','Unknown legacy method'
    class PaymentStatus(models.TextChoices):
        PENDING='pending','Pending'; AUTHORIZED='authorized','Authorized'; PAID='paid','Paid'; FAILED='failed','Failed'; CANCELLED='cancelled','Cancelled'; REFUNDED='refunded','Refunded'; UNKNOWN='unknown','Unknown legacy state'

    store=models.ForeignKey(Store,on_delete=models.CASCADE,related_name='orders')
    customer=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='customer_orders')
    order_number=models.CharField(max_length=40,unique=True,default=generate_order_number)
    status=models.CharField(max_length=16,choices=Status.choices,default=Status.PLACED)
    total=models.DecimalField(max_digits=12,decimal_places=2)
    subtotal=models.DecimalField(max_digits=12,decimal_places=2,null=True,blank=True)
    delivery_charge=models.DecimalField(max_digits=12,decimal_places=2,null=True,blank=True)
    currency=models.CharField(max_length=3,blank=True,default='')
    customer_name=models.CharField(max_length=180,blank=True)
    customer_phone=models.CharField(max_length=32,blank=True)
    delivery_address=models.JSONField(default=dict,blank=True)
    payment_method=models.CharField(max_length=16,choices=PaymentMethod.choices,default=PaymentMethod.LEGACY)
    payment_status=models.CharField(max_length=16,choices=PaymentStatus.choices,default=PaymentStatus.PENDING)
    idempotency_key=models.CharField(max_length=64,null=True,blank=True,unique=True)
    request_fingerprint=models.CharField(max_length=64,blank=True,default='')
    stock_reserved=models.BooleanField(default=False)
    razorpay_order_id=models.CharField(max_length=80,null=True,blank=True,unique=True)
    razorpay_payment_id=models.CharField(max_length=80,null=True,blank=True,unique=True)
    is_demo=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)


class OrderStatusHistory(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='status_history')
    from_status=models.CharField(max_length=16,blank=True)
    to_status=models.CharField(max_length=16,choices=Order.Status.choices)
    changed_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='order_status_changes')
    created_at=models.DateTimeField(auto_now_add=True)
    note=models.CharField(max_length=240,blank=True)

class OrderItem(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='items')
    product=models.ForeignKey(Product,on_delete=models.PROTECT,related_name='order_items')
    name=models.CharField(max_length=180)
    quantity=models.PositiveIntegerField()
    unit_price=models.DecimalField(max_digits=12,decimal_places=2)
