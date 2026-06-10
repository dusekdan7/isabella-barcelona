from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Cliente"
        ADMIN    = "ADMIN",    "Administrador"
        SUPPORT  = "SUPPORT",  "Soporte"

    email             = models.EmailField(unique=True)
    customer_number   = models.CharField(max_length=20, unique=True, blank=True, null=True)
    phone             = models.CharField(max_length=20, blank=True)
    street            = models.CharField(max_length=120, blank=True)
    city              = models.CharField(max_length=60, blank=True)
    postal_code       = models.CharField(max_length=10, blank=True)
    country           = models.CharField(max_length=2, default="ES")
    role              = models.CharField(max_length=10, choices=Role.choices, default=Role.CUSTOMER)
    is_verified       = models.BooleanField(default=False)
    accepts_marketing = models.BooleanField(default=False)

    USERNAME_FIELD  = "email"
    EMAIL_FIELD     = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name        = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>"


class Supplier(models.Model):
    name              = models.CharField(max_length=100)
    contact_email     = models.EmailField()
    api_endpoint      = models.URLField(max_length=255)
    api_key           = models.CharField(max_length=255)
    country           = models.CharField(max_length=2)
    avg_shipping_days = models.PositiveSmallIntegerField(default=7)
    is_active         = models.BooleanField(default=True)
    notes             = models.TextField(blank=True)

    class Meta:
        verbose_name        = "Proveedor"
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return self.name


class Product(models.Model):
    class Category(models.TextChoices):
        PENDIENTES = "PENDIENTES", "Pendientes"
        COLLARES   = "COLLARES",   "Collares"
        BRAZALETES = "BRAZALETES", "Brazaletes"
        ANILLOS    = "ANILLOS",    "Anillos"
        ACCESORIOS = "ACCESORIOS", "Accesorios"

    supplier         = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="products")
    sku              = models.CharField(max_length=50, unique=True)
    name_es          = models.CharField(max_length=150)
    name_en          = models.CharField(max_length=150, blank=True)
    description_es   = models.TextField(blank=True)
    category         = models.CharField(max_length=15, choices=Category.choices)
    cost_price       = models.DecimalField(max_digits=10, decimal_places=2)
    price            = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock_qty        = models.IntegerField(default=0)
    image_url        = models.URLField(max_length=500, blank=True)
    is_published     = models.BooleanField(default=True)
    weight           = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    slug             = models.SlugField(max_length=180, unique=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Producto"
        verbose_name_plural = "Productos"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"[{self.sku}] {self.name_es}"

    @property
    def is_on_sale(self):
        return self.compare_at_price is not None and self.compare_at_price > self.price


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    url     = models.URLField(max_length=500)
    order   = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering            = ['order']
        verbose_name        = "Imagen adicional"
        verbose_name_plural = "Imágenes adicionales"

    def __str__(self):
        return f"Imagen {self.order} — {self.product.name_es}"


class OrderItem(models.Model):
    order   = models.ForeignKey('Order', on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    qty     = models.PositiveIntegerField(default=1)
    price   = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name        = "Línea de pedido"
        verbose_name_plural = "Líneas de pedido"

    def __str__(self):
        return f"{self.qty}× {self.product.name_es}"

    @property
    def subtotal(self):
        return round(self.price * self.qty, 2)


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING   = "PENDING",   "Pendiente"
        PAID      = "PAID",      "Pagado"
        SHIPPED   = "SHIPPED",   "Enviado"
        DELIVERED = "DELIVERED", "Entregado"
        CANCELLED = "CANCELLED", "Cancelado"

    class Payment(models.TextChoices):
        STRIPE = "STRIPE", "Stripe"
        PAYPAL = "PAYPAL", "PayPal"
        COD    = "COD",    "Contra reembolso"

    order_number     = models.CharField(max_length=20, unique=True)
    user             = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    guest_email      = models.EmailField(blank=True)
    status           = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    total_amount     = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee     = models.DecimalField(max_digits=6, decimal_places=2, default=4.90)
    payment_method   = models.CharField(max_length=10, choices=Payment.choices)
    shipping_name    = models.CharField(max_length=120)
    shipping_street  = models.CharField(max_length=120)
    shipping_city    = models.CharField(max_length=60)
    shipping_postal  = models.CharField(max_length=10)
    shipping_country = models.CharField(max_length=2, default="ES")
    tracking_number  = models.CharField(max_length=100, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"{self.order_number} — {self.get_status_display()}"