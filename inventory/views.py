import hmac

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import Order
from .packing import OrderTooLarge, recommend_box


def recommendation_payload(order):
    """Plain-dict result shared by the API view and the management command."""
    result = recommend_box(order)
    if result is None:
        return {"order": order.reference, "box": None}
    box = result.box
    return {
        "order": order.reference,
        "box": {
            "id": box.pk,
            "name": box.name,
            "cost": str(box.cost),
            "internal_cm": [str(box.length_cm), str(box.width_cm), str(box.height_cm)],
            "max_weight_kg": str(box.max_weight_kg),
        },
        "total_weight_kg": str(result.total_weight_kg),
        "total_volume_cm3": str(result.total_volume_cm3),
    }


@require_GET
def order_box(request, reference):
    """GET /orders/<reference>/box/ -> recommended box as JSON."""
    expected_token = settings.BOX_API_TOKEN
    if expected_token:
        supplied_token = request.headers.get("Authorization", "")
        if not hmac.compare_digest(supplied_token, f"Bearer {expected_token}"):
            return JsonResponse({"error": "Authentication required."}, status=401)

    try:
        order = Order.objects.get(reference=reference)
    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found."}, status=404)
    try:
        payload = recommendation_payload(order)
    except OrderTooLarge as exc:
        return JsonResponse({"error": str(exc)}, status=422)
    return JsonResponse(payload)
