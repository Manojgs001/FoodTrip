from django.urls import path
from . import views

urlpatterns = [
    # ── Public ──────────────────────────────────────────────────────────────
    path('', views.index, name='index'),
    path('open_signin', views.open_signin, name='open_signin'),
    path('open_signup', views.open_signup, name='open_signup'),
    path('signup', views.signup, name='signup'),
    path('signin', views.signin, name='signin'),
    path('logout', views.logout, name='logout'),

    # ── Customer (session-based, no username in URL) ─────────────────────
    path('home/', views.customer_home, name='customer_home'),
    path('menu/<int:restaurant_id>/', views.view_menu, name='view_menu'),
    path('add_to_cart/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update_cart_quantity/<int:item_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('cart/', views.show_cart, name='show_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.orders, name='orders'),
    path('order_history/', views.order_history, name='order_history'),
    path('crave_detector/', views.crave_detector, name='crave_detector'),
    path('profile/', views.profile, name='profile'),

    # ── Admin ────────────────────────────────────────────────────────────
    path('open_add_restaurant', views.open_add_restaurant, name='open_add_restaurant'),
    path('add_restaurant', views.add_restaurant, name='add_restaurant'),
    path('open_show_restaurant', views.open_show_restaurant, name='open_show_restaurant'),
    path('open_update_restaurant/<int:restaurant_id>', views.open_update_restaurant, name='open_update_restaurant'),
    path('update_restaurant/<int:restaurant_id>', views.update_restaurant, name='update_restaurant'),
    path('delete_restaurant/<int:restaurant_id>', views.delete_restaurant, name='delete_restaurant'),
    path('open_update_menu/<int:restaurant_id>', views.open_update_menu, name='open_update_menu'),
    path('update_menu/<int:restaurant_id>', views.update_menu, name='update_menu'),
    path('edit_menu_item/<int:item_id>', views.edit_menu_item, name='edit_menu_item'),
    path('delete_menu_item/<int:item_id>', views.delete_menu_item, name='delete_menu_item'),
    path('admin_orders/', views.admin_orders, name='admin_orders'),
    path('update_order_status/<int:order_id>', views.update_order_status, name='update_order_status'),
    path('rate_restaurant/<int:restaurant_id>/', views.rate_restaurant, name='rate_restaurant'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
