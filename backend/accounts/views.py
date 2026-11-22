from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils.crypto import get_random_string

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token as google_id_token

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer


def token_response(user, response_status=status.HTTP_200_OK):
    refresh = RefreshToken.for_user(user)
    return Response(
        {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        },
        status=response_status,
    )


class RegisterView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return token_response(user, status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return token_response(serializer.validated_data["user"])


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        credential = request.data.get("credential")
        if not isinstance(credential, str) or not credential:
            return Response(
                {"detail": "A Google sign-in credential is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not settings.GOOGLE_CLIENT_ID:
            return Response(
                {"detail": "Google sign-in is not configured on this server."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            claims = google_id_token.verify_oauth2_token(
                credential,
                GoogleRequest(),
                settings.GOOGLE_CLIENT_ID,
            )
        except (GoogleAuthError, ValueError):
            return Response(
                {"detail": "The Google sign-in credential is invalid or expired."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        email = claims.get("email")
        if (
            not isinstance(email, str)
            or not email.strip()
            or claims.get("email_verified") is not True
        ):
            return Response(
                {"detail": "Google must provide a verified email address."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        email = email.strip().lower()
        user_model = get_user_model()
        user = user_model.objects.filter(email__iexact=email).first()
        if user is None:
            given_name = claims.get("given_name", "")
            family_name = claims.get("family_name", "")
            try:
                username = (
                    f"{email.split('@', 1)[0][:140]}-"
                    f"{get_random_string(8)}"
                )
                user = user_model.objects.create_user(
                    username=username,
                    email=email,
                    password=None,
                    first_name=given_name[:150] if isinstance(given_name, str) else "",
                    last_name=family_name[:150] if isinstance(family_name, str) else "",
                )
            except IntegrityError:
                user = user_model.objects.filter(email__iexact=email).first()
                if user is None:
                    raise

        if not user.is_active:
            return Response(
                {"detail": "This account is inactive."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return token_response(user)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
