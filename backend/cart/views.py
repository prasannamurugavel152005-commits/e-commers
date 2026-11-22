from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from products.models import Product

from .models import Cart, CartItem
from .serializers import CartItemSerializer


class AddCartItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, default=1)


class CartQuantitySerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class GuestCartItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)


class GuestCartSyncSerializer(serializers.Serializer):
    items = GuestCartItemSerializer(many=True)

    def validate_items(self, items):
        product_ids = [item["product_id"] for item in items]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError(
                "Each product may only appear once."
            )
        return items


def cart_response(user):
    cart = Cart.objects.filter(user=user).first()
    if cart is None:
        return {"items": [], "total": Decimal("0.00")}

    items = list(
        CartItem.objects.filter(cart=cart)
        .select_related("product", "product__category")
        .order_by("id")
    )
    total = sum(
        (item.product.price * item.quantity for item in items),
        Decimal("0.00"),
    )
    return {"items": CartItemSerializer(items, many=True).data, "total": total}


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(cart_response(request.user))


class CartSyncView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GuestCartSyncSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        requested_items = serializer.validated_data["items"]

        with transaction.atomic():
            cart, _ = Cart.objects.select_for_update().get_or_create(
                user=request.user
            )
            product_ids = [item["product_id"] for item in requested_items]
            products = {
                product.pk: product
                for product in Product.objects.select_for_update()
                .filter(pk__in=product_ids, is_active=True)
                .order_by("pk")
            }
            if len(products) != len(requested_items):
                return Response(
                    {"detail": "A product in your saved cart is unavailable."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            existing_items = {
                item.product_id: item
                for item in CartItem.objects.select_for_update().filter(
                    cart=cart,
                    product_id__in=product_ids,
                )
            }
            merged_quantities = {}
            for requested in requested_items:
                product_id = requested["product_id"]
                existing = existing_items.get(product_id)
                quantity = max(
                    requested["quantity"],
                    existing.quantity if existing else 0,
                )
                if quantity > products[product_id].stock:
                    return Response(
                        {
                            "detail": (
                                f"Only {products[product_id].stock} units of "
                                f"{products[product_id].name} are available."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                merged_quantities[product_id] = quantity

            for product_id, quantity in merged_quantities.items():
                item = existing_items.get(product_id)
                if item is None:
                    CartItem.objects.create(
                        cart=cart,
                        product=products[product_id],
                        quantity=quantity,
                    )
                elif item.quantity != quantity:
                    item.quantity = quantity
                    item.save(update_fields=["quantity"])

        return Response(cart_response(request.user))


class CartAddView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_id = serializer.validated_data["product_id"]
        quantity = serializer.validated_data["quantity"]

        with transaction.atomic():
            cart, _ = Cart.objects.select_for_update().get_or_create(
                user=request.user
            )
            product = get_object_or_404(
                Product.objects.select_for_update(),
                pk=product_id,
                is_active=True,
            )
            item = CartItem.objects.select_for_update().filter(
                cart=cart,
                product=product,
            ).first()
            next_quantity = quantity + (item.quantity if item else 0)
            if next_quantity > product.stock:
                return Response(
                    {"detail": "The requested quantity is not available."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if item is None:
                CartItem.objects.create(
                    cart=cart,
                    product=product,
                    quantity=next_quantity,
                )
            else:
                item.quantity = next_quantity
                item.save(update_fields=["quantity"])

        return Response(cart_response(request.user), status=status.HTTP_200_OK)


class CartItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, item_id):
        serializer = CartQuantitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quantity = serializer.validated_data["quantity"]

        with transaction.atomic():
            item = get_object_or_404(
                CartItem.objects.select_for_update().filter(
                    cart__user=request.user
                ),
                pk=item_id,
            )
            product = get_object_or_404(
                Product.objects.select_for_update(),
                pk=item.product_id,
                is_active=True,
            )
            if quantity > product.stock:
                return Response(
                    {"detail": "The requested quantity is not available."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            item.quantity = quantity
            item.save(update_fields=["quantity"])

        return Response(cart_response(request.user))

    def delete(self, request, item_id):
        with transaction.atomic():
            item = get_object_or_404(
                CartItem.objects.select_for_update().filter(
                    cart__user=request.user
                ),
                pk=item_id,
            )
            item.delete()
        return Response(cart_response(request.user))
