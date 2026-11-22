"""
URL configuration for ecommerce_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from ecommerce_backend.views import api_root
from accounts.views import GoogleLoginView, LoginView, ProfileView, RegisterView
from rest_framework_simplejwt.views import TokenRefreshView
from products.views import CategoryListView, ProductListView
from cart.views import CartAddView, CartItemDetailView, CartSyncView, CartView
from orders.views import CheckoutView, OrderDetailView, OrderListView

urlpatterns = [
    path("", api_root, name="api-root"),
    path("api/", api_root, name="api-index"),
    path("admin/", admin.site.urls),
    path("api/accounts/register/", RegisterView.as_view(), name="account-register"),
    path("api/accounts/login/", LoginView.as_view(), name="account-login"),
    path("api/accounts/google/", GoogleLoginView.as_view(), name="google-login"),
    path("api/accounts/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/accounts/profile/", ProfileView.as_view(), name="account-profile"),
    path("api/products/categories/", CategoryListView.as_view(), name="category-list"),
    path("api/products/", ProductListView.as_view(), name="product-list"),
    path(
        "api/products/products/",
        ProductListView.as_view(),
        name="product-list-compatibility",
    ),
    path("api/cart/", CartView.as_view(), name="cart"),
    path("api/cart/add/", CartAddView.as_view(), name="cart-add"),
    path("api/cart/sync/", CartSyncView.as_view(), name="cart-sync"),
    path(
        "api/cart/items/<int:item_id>/",
        CartItemDetailView.as_view(),
        name="cart-item-detail",
    ),
    path("api/orders/checkout/", CheckoutView.as_view(), name="order-checkout"),
    path("api/orders/", OrderListView.as_view(), name="order-list"),
    path(
        "api/orders/<int:order_id>/",
        OrderDetailView.as_view(),
        name="order-detail",
    ),
]
