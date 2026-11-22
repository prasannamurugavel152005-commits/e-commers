from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Cart, CartItem
from products.models import Category, Product


class CartApiTests(APITestCase):
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
        self.client.force_authenticate(self.user)

    def test_customer_can_add_and_update_cart_quantity(self):
        added = self.client.post(
            "/api/cart/add/",
            {"product_id": self.product.pk, "quantity": 2},
            format="json",
        )

        self.assertEqual(added.status_code, status.HTTP_200_OK)
        self.assertEqual(added.data["items"][0]["product"]["id"], self.product.pk)
        self.assertEqual(added.data["items"][0]["quantity"], 2)

        item_id = added.data["items"][0]["id"]
        updated = self.client.put(
            f"/api/cart/items/{item_id}/",
            {"quantity": 3},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["items"][0]["quantity"], 3)
        self.assertEqual(str(updated.data["total"]), "300.00")

    def test_customer_cannot_read_or_change_another_users_cart_item(self):
        other_cart = Cart.objects.create(user=self.other_user)
        item = CartItem.objects.create(
            cart=other_cart,
            product=self.product,
            quantity=1,
        )

        response = self.client.put(
            f"/api/cart/items/{item.pk}/",
            {"quantity": 4},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)

    def test_add_rejects_unavailable_quantity_without_creating_item(self):
        response = self.client.post(
            "/api/cart/add/",
            {"product_id": self.product.pk, "quantity": 6},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(CartItem.objects.exists())

    def test_guest_cart_sync_is_safe_to_retry(self):
        CartItem.objects.create(
            cart=Cart.objects.create(user=self.user),
            product=self.product,
            quantity=2,
        )
        payload = {
            "items": [{"product_id": self.product.pk, "quantity": 4}],
        }

        first = self.client.post("/api/cart/sync/", payload, format="json")
        second = self.client.post("/api/cart/sync/", payload, format="json")

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(CartItem.objects.get().quantity, 4)
