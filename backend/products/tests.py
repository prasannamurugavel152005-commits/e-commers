from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Product


class ProductCatalogApiTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics",
        )
        for index in range(31):
            Product.objects.create(
                category=self.category,
                name=f"Device {index}",
                slug=f"device-{index}",
                description="Everyday electronics",
                price=Decimal("1299.00"),
                compare_at_price=Decimal("1599.00"),
                image_url="https://example.com/device.jpg",
                image_source_url="https://commons.wikimedia.org/wiki/File:Device.jpg",
                image_attribution="Commons photographer",
                image_license="CC BY-SA 4.0",
            )

    def test_products_can_be_filtered_and_categories_report_counts(self):
        response = self.client.get("/api/products/?category=electronics")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 31)
        self.assertEqual(response.data["results"][0]["category"], "Electronics")
        self.assertEqual(
            response.data["results"][0]["image_attribution"],
            "Commons photographer",
        )
        self.assertEqual(
            response.data["results"][0]["image_license"],
            "CC BY-SA 4.0",
        )

        compatibility_response = self.client.get(
            "/api/products/products/?category=electronics"
        )
        self.assertEqual(
            compatibility_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            compatibility_response.data["results"],
            response.data["results"],
        )

        categories = self.client.get("/api/products/categories/")
        self.assertEqual(categories.status_code, status.HTTP_200_OK)
        self.assertEqual(categories.data["results"][0]["product_count"], 31)


class SeedProductImageTests(TestCase):
    def test_seed_command_assigns_a_unique_image_to_each_product(self):
        call_command("seed_products", stdout=StringIO())

        self.assertEqual(Product.objects.count(), 128)
        self.assertEqual(
            Product.objects.values("image_url").distinct().count(),
            128,
        )
        self.assertEqual(
            Product.objects.filter(image_attribution="").count(),
            0,
        )
        self.assertEqual(
            Product.objects.filter(image_source_url="").count(),
            0,
        )
        self.assertEqual(
            Product.objects.filter(image_license="").count(),
            0,
        )

    def test_api_root_reports_available_endpoints(self):
        for endpoint in ("/", "/api/"):
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.json()["status"], "ok")
                self.assertIn("products", response.json()["endpoints"])
