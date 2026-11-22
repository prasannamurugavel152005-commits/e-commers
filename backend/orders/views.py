from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.models import Cart, CartItem
from products.models import Product

from .models import Order, OrderItem
from .serializers import OrderSerializer


class CheckoutSerializer(serializers.Serializer):
    address = serializers.CharField(max_length=500)
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=100, default="India")
    phone = serializers.CharField(max_length=20)


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.prefetch_related("items").order_by(
            "-created_at",
            "-id",
        )
        if not request.user.is_staff:
            orders = orders.filter(user=request.user)
        return Response(OrderSerializer(orders, many=True).data)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        orders = Order.objects.prefetch_related("items")
        if not request.user.is_staff:
            orders = orders.filter(user=request.user)
        order = get_object_or_404(orders, pk=order_id)
        return Response(OrderSerializer(order).data)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shipping = serializer.validated_data

        with transaction.atomic():
            cart = Cart.objects.select_for_update().filter(
                user=request.user
            ).first()
            if cart is None:
                return Response(
                    {"detail": "Your cart is empty."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cart_items = list(
                CartItem.objects.select_for_update()
                .filter(cart=cart)
                .order_by("product_id")
            )
            if not cart_items:
                return Response(
                    {"detail": "Your cart is empty."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            product_ids = [item.product_id for item in cart_items]
            products = {
                product.pk: product
                for product in Product.objects.select_for_update()
                .filter(pk__in=product_ids, is_active=True)
                .order_by("pk")
            }
            if len(products) != len(cart_items):
                return Response(
                    {"detail": "A product in your cart is no longer available."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            total = Decimal("0.00")
            for item in cart_items:
                product = products[item.product_id]
                if item.quantity > product.stock:
                    return Response(
                        {
                            "detail": (
                                f"Only {product.stock} units of "
                                f"{product.name} are available."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                total += product.price * item.quantity

            order = Order.objects.create(
                user=request.user,
                total_amount=total,
                shipping_address=shipping["address"],
                shipping_city=shipping["city"],
                shipping_state=shipping["state"],
                shipping_postal_code=shipping["postal_code"],
                shipping_country=shipping["country"],
                shipping_phone=shipping["phone"],
            )
            OrderItem.objects.bulk_create(
                [
                    OrderItem(
                        order=order,
                        product=products[item.product_id],
                        product_name=products[item.product_id].name,
                        unit_price=products[item.product_id].price,
                        quantity=item.quantity,
                    )
                    for item in cart_items
                ]
            )
            for item in cart_items:
                product = products[item.product_id]
                product.stock -= item.quantity
                product.save(update_fields=["stock"])
            cart.items.all().delete()

        order = Order.objects.prefetch_related("items").get(pk=order.pk)
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )
