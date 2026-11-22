from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from cart.models import Cart, CartItem
from products.models import Category, Product

from .models import Order, OrderItem


class OrderApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="customer",
            email="customer@example.com",
            password="Shopper-Password-92!",
        )
        self.other_user = get_user_model().objects.create_user(
            username="other",
            email="other@example.com",
            password="Shopper-Password-92!",
        )
        category = Category.objects.create(name="Home", slug="home")
        self.product = Product.objects.create(
            category=category,
            name="Table lamp",
            slug="table-lamp",
            description="A warm desk lamp",
            price="100.00",
            compare_at_price="120.00",
            stock=5,
            image_url="https://example.com/lamp.jpg",
        )
        self.cart = Cart.objects.create(user=self.user)
        self.client.force_authenticate(self.user)
        self.shipping = {
            "address": "12 Market Street",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "postal_code": "600001",
            "country": "India",
            "phone": "9876543210",
        }

    def test_checkout_creates_order_decrements_stock_and_empties_cart(self):
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)

        response = self.client.post(
            "/api/orders/checkout/",
            self.shipping,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["total_amount"], "200.00")
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["product_name"], "Table lamp")
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertFalse(CartItem.objects.filter(cart=self.cart).exists())
        self.assertEqual(Order.objects.filter(user=self.user).count(), 1)

    def test_checkout_with_insufficient_stock_changes_nothing(self):
        second_product = Product.objects.create(
            category=self.product.category,
            name="Floor lamp",
            slug="floor-lamp",
            description="A floor lamp",
            price="250.00",
            compare_at_price="300.00",
            stock=0,
            image_url="https://example.com/floor-lamp.jpg",
        )
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        CartItem.objects.create(cart=self.cart, product=second_product, quantity=1)

        response = self.client.post(
            "/api/orders/checkout/",
            self.shipping,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        self.assertFalse(Order.objects.exists())
        self.assertEqual(CartItem.objects.filter(cart=self.cart).count(), 2)

    def test_customer_cannot_access_another_users_order(self):
        order = Order.objects.create(
            user=self.other_user,
            total_amount="100.00",
            shipping_address="1 Private Lane",
            shipping_city="Chennai",
            shipping_state="Tamil Nadu",
            shipping_postal_code="600001",
            shipping_country="India",
            shipping_phone="9876543210",
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            unit_price=self.product.price,
            quantity=1,
        )

        detail = self.client.get(f"/api/orders/{order.pk}/")
        listing = self.client.get("/api/orders/")

        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.data, [])

    def test_checkout_requires_nonempty_cart(self):
        response = self.client.post(
            "/api/orders/checkout/",
            self.shipping,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Order.objects.exists())
