from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def api_root(_request):
    return JsonResponse(
        {
            "service": "Pexo Market API",
            "status": "ok",
            "endpoints": {
                "categories": "/api/products/categories/",
                "products": "/api/products/",
                "products_compatibility": "/api/products/products/",
                "register": "/api/accounts/register/",
                "login": "/api/accounts/login/",
            },
        }
    )
