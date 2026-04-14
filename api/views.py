import json
import re
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from api.services.google_places import search_places_without_website, PLACE_CATEGORIES
from api.services.ai_chat import chat_with_ai
from api.services.locations import get_locations, get_supported_countries, validate_location, AREA_RADIUS


@require_GET
def get_categories(request):
    return JsonResponse({"categories": list(PLACE_CATEGORIES.keys())})


@require_GET
def countries(request):
    return JsonResponse({"countries": get_supported_countries()})


@require_GET
def locations(request, country_code):
    result = get_locations(country_code.upper())
    if "error" in result:
        return JsonResponse(result, status=404)
    return JsonResponse(result)


@csrf_exempt
@require_POST
def search_places(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    latitude = data.get("latitude")
    longitude = data.get("longitude")
    category = data.get("category")
    radius = data.get("radius", 4000)

    if latitude is None or longitude is None:
        return JsonResponse({"error": "Latitude and longitude are required"}, status=400)

    if category is None:
        return JsonResponse({"error": "Category is required"}, status=400)

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        radius = int(radius)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid coordinates or radius"}, status=400)

    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        return JsonResponse({"error": "Coordinates out of range"}, status=400)

    if not (100 <= radius <= 5000):
        return JsonResponse({"error": "Radius must be between 100 and 5000"}, status=400)

    if category not in PLACE_CATEGORIES:
        return JsonResponse({"error": f"Invalid category. Valid: {list(PLACE_CATEGORIES.keys())}"}, status=400)

    result = search_places_without_website(latitude, longitude, category, radius)

    if "error" in result:
        return JsonResponse(result, status=502)

    return JsonResponse(result)


@csrf_exempt
@require_POST
def search_by_area(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    country_code = data.get("country_code")
    area_type = data.get("area_type")
    area_name = data.get("area_name")
    category = data.get("category")

    if not all([country_code, area_type, area_name, category]):
        return JsonResponse({"error": "country_code, area_type, area_name and category are required"}, status=400)

    if area_type not in ("metro", "cadde", "rayon"):
        return JsonResponse({"error": "area_type must be metro, cadde or rayon"}, status=400)

    if category not in PLACE_CATEGORIES:
        return JsonResponse({"error": f"Invalid category. Valid: {list(PLACE_CATEGORIES.keys())}"}, status=400)

    location = validate_location(country_code.upper(), area_type, area_name)
    if not location:
        return JsonResponse({"error": "Invalid location selection"}, status=400)

    radius = AREA_RADIUS.get(area_type, 1000)
    result = search_places_without_website(location["latitude"], location["longitude"], category, radius)

    if "error" in result:
        return JsonResponse(result, status=502)

    return JsonResponse(result)


@csrf_exempt
@require_POST
def chat(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    messages = data.get("messages")
    business_info = data.get("business_info")
    competitors = data.get("competitors")

    if not messages or not isinstance(messages, list):
        return JsonResponse({"error": "Messages list is required"}, status=400)

    if len(messages) > 50:
        return JsonResponse({"error": "Too many messages"}, status=400)

    for msg in messages:
        if msg.get("role") not in ("user", "assistant"):
            return JsonResponse({"error": "Invalid message role"}, status=400)
        content = msg.get("content", "")
        if not content or len(content) > 1000:
            return JsonResponse({"error": "Message is empty or too long (max 1000 characters)"}, status=400)
        msg["content"] = re.sub(r'<[^>]+>', '', content)

    result = chat_with_ai(messages, business_info, competitors)

    if "error" in result:
        return JsonResponse(result, status=502)

    return JsonResponse(result)