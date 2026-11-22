from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase


class AccountApiTests(APITestCase):
    def test_google_sign_in_requires_server_configuration(self):
        with override_settings(GOOGLE_CLIENT_ID=""):
            response = self.client.post(
                "/api/accounts/google/",
                {"credential": "google-id-token"},
                format="json",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
        self.assertIn("not configured", response.data["detail"])

    @patch("accounts.views.google_id_token.verify_oauth2_token")
    def test_google_sign_in_verifies_email_and_issues_jwt(self, verify_token):
        verify_token.return_value = {
            "email": "google-customer@example.com",
            "email_verified": True,
            "given_name": "Google",
            "family_name": "Customer",
        }

        with override_settings(GOOGLE_CLIENT_ID="test-client-id"):
            response = self.client.post(
                "/api/accounts/google/",
                {"credential": "valid-google-id-token"},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertEqual(
            response.data["user"]["email"],
            "google-customer@example.com",
        )
        user = get_user_model().objects.get(email="google-customer@example.com")
        self.assertFalse(user.has_usable_password())
        verify_token.assert_called_once()

    @patch("accounts.views.google_id_token.verify_oauth2_token")
    def test_google_sign_in_rejects_unverified_email(self, verify_token):
        verify_token.return_value = {
            "email": "unverified@example.com",
            "email_verified": False,
        }

        with override_settings(GOOGLE_CLIENT_ID="test-client-id"):
            response = self.client.post(
                "/api/accounts/google/",
                {"credential": "validly-signed-unverified-token"},
                format="json",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertFalse(
            get_user_model().objects.filter(email="unverified@example.com").exists()
        )

    def test_customer_can_register_login_and_read_profile(self):
        registration = self.client.post(
            "/api/accounts/register/",
            {
                "email": "customer@example.com",
                "password": "Shopper-Password-92!",
                "password_confirm": "Shopper-Password-92!",
                "first_name": "Casey",
                "last_name": "Customer",
            },
            format="json",
        )

        self.assertEqual(registration.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", registration.data)
        self.assertEqual(registration.data["user"]["email"], "customer@example.com")

        login = self.client.post(
            "/api/accounts/login/",
            {"email": "CUSTOMER@example.com", "password": "Shopper-Password-92!"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login.data['access']}"
        )
        profile = self.client.get("/api/accounts/profile/")
        self.assertEqual(profile.status_code, status.HTTP_200_OK)
        self.assertEqual(profile.data["first_name"], "Casey")

    def test_invalid_login_does_not_authenticate(self):
        get_user_model().objects.create_user(
            username="customer",
            email="customer@example.com",
            password="Shopper-Password-92!",
        )

        response = self.client.post(
            "/api/accounts/login/",
            {"email": "customer@example.com", "password": "incorrect"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("access", response.data)

    def test_profile_requires_authentication(self):
        response = self.client.get("/api/accounts/profile/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
