from django.db.models import Count, Q
from rest_framework import generics
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from .models import Category, Product


class CategorySerializer(ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "product_count"]


class ProductSerializer(ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True)
    detail = serializers.CharField(source="description", read_only=True)
    oldPrice = serializers.DecimalField(
        source="compare_at_price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    reviews = serializers.IntegerField(source="review_count", read_only=True)
    image = serializers.URLField(source="image_url", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "detail",
            "category",
            "price",
            "oldPrice",
            "rating",
            "reviews",
            "badge",
            "image",
            "image_source_url",
            "image_attribution",
            "image_license",
            "image_license_url",
        ]


class CategoryListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.annotate(
            product_count=Count("products", filter=Q(products__is_active=True))
        ).order_by("name")


class ProductListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "description", "category__name"]
    ordering_fields = ["price", "rating", "name", "created_at"]
    ordering = ["id"]

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related("category")
        category = self.request.query_params.get("category")
        if category and category.lower() != "all":
            queryset = queryset.filter(category__slug=category)
        return queryset
