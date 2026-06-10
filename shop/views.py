import random
import string
from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib import messages
from .models import Product, Order, OrderItem


# ---------- SHOP ----------

def index(request):
    products = Product.objects.all()[:8]
    return render(request, 'index.html', {'products': products})


_SORT_MAP = {
    'price_asc':  'price',
    'price_desc': '-price',
    'newest':     '-created_at',
}

_CATEGORY_CHOICES = [
    ('PENDIENTES',  'Pendientes'),
    ('COLLARES',    'Collares'),
    ('ANILLOS',     'Anillos'),
    ('BRAZALETES',  'Brazaletes'),
    ('ACCESORIOS',  'Accesorios'),
]

def coleccion(request):
    category = request.GET.get('category', '')
    sort     = request.GET.get('sort', 'newest')
    qs = Product.objects.filter(is_published=True)
    if category:
        qs = qs.filter(category=category)
    qs = qs.order_by(_SORT_MAP.get(sort, '-created_at'))
    return render(request, 'coleccion.html', {
        'products':         qs,
        'active_category':  category,
        'active_sort':      sort,
        'category_choices': _CATEGORY_CHOICES,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related = Product.objects.exclude(id=product.id)[:4]
    return render(request, 'product_detail.html', {'product': product, 'related': related})


# ---------- CARRITO ----------

def carrito(request):
    cart = request.session.get('cart', {})
    items = []
    total = 0
    for product_id, qty in cart.items():
        try:
            p = Product.objects.get(id=int(product_id))
            subtotal = p.price * qty
            total += subtotal
            items.append({'product': p, 'qty': qty, 'subtotal': round(subtotal, 2)})
        except Product.DoesNotExist:
            pass
    total = round(total, 2)
    needed = round(max(0, 100 - float(total)), 2)
    return render(request, 'carrito.html', {
        'items': items, 'total': total, 'needed': needed,
        'free_threshold': Decimal('100'),
    })


def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    key = str(product_id)
    try:
        qty = max(1, int(request.POST.get('qty', 1)))
    except (ValueError, TypeError):
        qty = 1
    cart[key] = cart.get(key, 0) + qty
    request.session['cart'] = cart
    request.session.modified = True
    messages.success(request, 'Producto añadido al carrito ✓')
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER', '/')
    return redirect(next_url)


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    key = str(product_id)
    if key in cart:
        del cart[key]
        request.session['cart'] = cart
        request.session.modified = True
    return redirect('carrito')


def update_cart(request, product_id):
    cart = request.session.get('cart', {})
    key = str(product_id)
    qty = int(request.POST.get('qty', 1))
    if qty > 0:
        cart[key] = qty
    else:
        cart.pop(key, None)
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('carrito')


# ---------- AUTH ----------

def login_view(request):
    if request.user.is_authenticated:
        return redirect('mi_cuenta')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('mi_cuenta')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    return render(request, 'login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('mi_cuenta')
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Este nombre de usuario ya existe.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password1)
            login(request, user)
            messages.success(request, '¡Bienvenida a Isabella Barcelona!')
            return redirect('mi_cuenta')
    return render(request, 'register.html')


def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('carrito')

    items = []
    subtotal = Decimal('0')
    for product_id, qty in cart.items():
        try:
            p = Product.objects.get(id=int(product_id))
            item_total = p.price * qty
            subtotal += item_total
            items.append({'product': p, 'qty': qty, 'subtotal': round(item_total, 2)})
        except Product.DoesNotExist:
            pass

    if not items:
        return redirect('carrito')

    subtotal      = round(subtotal, 2)
    shipping_fee  = Decimal('0') if subtotal >= 100 else Decimal('3.90')
    grand_total   = round(subtotal + shipping_fee, 2)

    form_data = {}

    if request.method == 'POST':
        form_data = {k: request.POST.get(k, '').strip() for k in
                     ('name', 'email', 'phone', 'street', 'city', 'postal', 'country', 'payment')}
        form_data.setdefault('country', 'ES')
        form_data.setdefault('payment', 'STRIPE')

        required = {'name': 'El nombre completo', 'email': 'El email',
                    'street': 'La dirección', 'city': 'La ciudad', 'postal': 'El código postal'}
        errors = [f'{label} es obligatorio.' for field, label in required.items() if not form_data.get(field)]

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            order_number = 'IB' + ''.join(random.choices(string.digits, k=8))
            user = request.user if request.user.is_authenticated else None
            order = Order.objects.create(
                order_number   = order_number,
                user           = user,
                guest_email    = form_data['email'] if not user else '',
                total_amount   = grand_total,
                shipping_fee   = shipping_fee,
                payment_method = form_data['payment'],
                shipping_name  = form_data['name'],
                shipping_street= form_data['street'],
                shipping_city  = form_data['city'],
                shipping_postal= form_data['postal'],
                shipping_country=form_data['country'],
            )
            for item in items:
                OrderItem.objects.create(
                    order=order, product=item['product'],
                    qty=item['qty'], price=item['product'].price,
                )
            request.session['cart'] = {}
            request.session.modified = True
            return redirect('gracias', order_number=order_number)

    # Pre-fill from logged-in user
    if not form_data and request.user.is_authenticated:
        u = request.user
        form_data = {
            'name':    f'{u.first_name} {u.last_name}'.strip() or u.username,
            'email':   u.email,
            'phone':   u.phone,
            'street':  u.street,
            'city':    u.city,
            'postal':  u.postal_code,
            'country': u.country,
        }

    needed_checkout = Decimal(str(round(max(0, 100 - float(subtotal)), 2)))
    return render(request, 'checkout.html', {
        'items': items, 'subtotal': subtotal,
        'shipping_fee': shipping_fee, 'grand_total': grand_total,
        'needed_checkout': needed_checkout,
        'form': form_data,
    })


def gracias(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'gracias.html', {'order': order})


# ---------- STATIC PAGES ----------

def preguntas_frecuentes(request):
    return render(request, 'preguntas_frecuentes.html')

def nuestra_historia(request):
    return render(request, 'nuestra_historia.html')

def aviso_legal(request):
    return render(request, 'aviso_legal.html')

def condiciones_venta(request):
    return render(request, 'condiciones_venta.html')

def politica_devoluciones(request):
    return render(request, 'politica_devoluciones.html')


def set_preferences(request):
    if request.method == 'POST':
        lang = request.POST.get('lang')
        currency = request.POST.get('currency')
        if lang in ('es', 'en', 'fr', 'de', 'it', 'cs'):
            request.session['site_lang'] = lang
        if currency in ('EUR', 'USD', 'GBP', 'CHF', 'PLN', 'CZK', 'SEK', 'NOK', 'DKK', 'AUD', 'CAD', 'JPY'):
            request.session['site_currency'] = currency
        request.session.modified = True
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER', '/')
    return redirect(next_url)


def logout_view(request):
    logout(request)
    return redirect('index')


@login_required(login_url='/login/')
def mi_cuenta(request):
    try:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
    except Exception:
        orders = []
    return render(request, 'mi_cuenta.html', {'orders': orders})