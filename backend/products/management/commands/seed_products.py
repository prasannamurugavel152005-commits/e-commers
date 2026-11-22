import json
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from products.models import Category, Product


CATALOG = {
    "Electronics": {
        "items": [
            "Wireless Headphones",
            "Bluetooth Speaker",
            "Smart Watch",
            "Digital Camera",
            "Portable Projector",
            "Power Bank",
            "USB-C Hub",
            "Desk Microphone",
        ],
        "price": 2499,
    },
    "Home": {
        "items": [
            "Table Lamp",
            "Knit Throw Blanket",
            "Ceramic Vase",
            "Accent Cushion Set",
            "Wall Clock",
            "Storage Basket",
            "Bedside Organizer",
            "Scented Candle Set",
        ],
        "price": 1299,
    },
    "Fashion": {
        "items": [
            "Everyday Backpack",
            "Classic Minimal Watch",
            "Canvas Weekend Bag",
            "Cloud Knit Sneakers",
            "Polarized Sunglasses",
            "Cotton Overshirt",
            "Leather Card Holder",
            "Everyday Crossbody Bag",
        ],
        "price": 1899,
    },
    "Kitchen": {
        "items": [
            "Coffee Maker",
            "Stoneware Dinner Set",
            "Insulated Travel Mug",
            "Chef Knife Set",
            "Cast Iron Skillet",
            "Glass Food Storage Set",
            "Electric Milk Frother",
            "Cotton Kitchen Towel Set",
        ],
        "price": 999,
    },
}

EDITIONS = ["Everyday", "Studio", "Travel", "Classic"]
BADGES = ["Bestseller", "Popular", "Top rated", "Just in"]
IMAGE_CATALOG_PATH = Path(__file__).resolve().parents[2] / "product_image_catalog.json"


class Command(BaseCommand):
    help = "Create 32 sample products for each storefront category."

    def handle(self, *args, **options):
        try:
            with IMAGE_CATALOG_PATH.open(encoding="utf-8") as image_file:
                image_catalog = json.load(image_file)
        except (OSError, json.JSONDecodeError) as error:
            raise CommandError(
                f"Could not load the product image catalog at {IMAGE_CATALOG_PATH}."
            ) from error

        created = 0
        for category_index, (category_name, config) in enumerate(CATALOG.items()):
            category, _ = Category.objects.get_or_create(
                slug=slugify(category_name),
                defaults={"name": category_name},
            )
            for item_index, item in enumerate(config["items"]):
                try:
                    image_options = image_catalog[category_name][item]
                except (KeyError, TypeError) as error:
                    raise CommandError(
                        f"Missing image catalog entry for {category_name}/{item}."
                    ) from error
                if len(image_options) != len(EDITIONS):
                    raise CommandError(
                        f"Expected {len(EDITIONS)} images for {category_name}/{item}."
                    )

                for edition_index, edition in enumerate(EDITIONS):
                    name = f"{edition} {item}"
                    price = config["price"] + item_index * 175 + edition_index * 125
                    slug = f"{slugify(name)}-{slugify(category_name)}"
                    image = image_options[edition_index]
                    required_fields = (
                        "image_url",
                        "image_source_url",
                        "image_attribution",
                        "image_license",
                    )
                    if any(not image.get(field) for field in required_fields):
                        raise CommandError(
                            f"Incomplete image attribution for {category_name}/{name}."
                        )
                    product, was_created = Product.objects.update_or_create(
                        slug=slug,
                        defaults={
                            "category": category,
                            "name": name,
                            "description": (
                                f"A thoughtfully designed {item.lower()} made "
                                "for your everyday."
                            ),
                            "price": Decimal(price),
                            "compare_at_price": Decimal(price * 5 // 4),
                            "stock": 20 + item_index,
                            "image_url": image["image_url"],
                            "image_source_url": image["image_source_url"],
                            "image_attribution": image["image_attribution"],
                            "image_license": image.get("image_license", ""),
                            "image_license_url": image.get("image_license_url", ""),
                            "rating": Decimal("4.2")
                            + Decimal((item_index + edition_index) % 8) / 10,
                            "review_count": 80 + item_index * 37 + edition_index * 11,
                            "badge": BADGES[(item_index + edition_index) % len(BADGES)],
                            "is_active": True,
                        },
                    )
                    created += int(was_created)
            self.stdout.write(f"{category_name}: {category.products.count()} products")

        self.stdout.write(
            self.style.SUCCESS(f"Catalog ready; added {created} new products.")
        )
