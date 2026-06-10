from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('coleccion/', views.coleccion, name='coleccion'),
    path('coleccion/<slug:slug>/', views.product_detail, name='product_detail'),

    # Carrito
    path('carrito/', views.carrito, name='carrito'),
    path('carrito/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('carrito/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('carrito/update/<int:product_id>/', views.update_cart, name='update_cart'),

    # Checkout
    path('checkout/', views.checkout, name='checkout'),
    path('gracias/<str:order_number>/', views.gracias, name='gracias'),

    # Static pages
    path('preguntas-frecuentes/',    views.preguntas_frecuentes, name='preguntas_frecuentes'),
    path('nuestra-historia/',        views.nuestra_historia,     name='nuestra_historia'),
    path('aviso-legal/',             views.aviso_legal,          name='aviso_legal'),
    path('condiciones-de-venta/',    views.condiciones_venta,    name='condiciones_venta'),
    path('politica-de-devoluciones/',views.politica_devoluciones,name='politica_devoluciones'),

    # Preferences
    path('set-preferences/', views.set_preferences, name='set_preferences'),

    # Auth
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('mi-cuenta/', views.mi_cuenta, name='mi_cuenta'),
]