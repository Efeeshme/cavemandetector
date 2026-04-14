import logging
import time
import hashlib
import requests
from django.conf import settings

logger = logging.getLogger("api")

PLACE_CATEGORIES = {
    "restaurant": "restaurant",
    "cafe": "cafe",
    "gym": "gym",
    "bar": "bar",
    "hotel": "hotel",
    "beauty_salon": "beauty_salon",
    "hair_care": "hair_care",
    "dentist": "dentist",
    "doctor": "doctor",
    "pharmacy": "pharmacy",
    "car_repair": "car_repair",
    "real_estate_agency": "real_estate_agency",
    "store": "store",
    "pet_store": "pet_store",
}

NEARBY_SEARCH_URL = "https://places.googleapis.com/v1/places:searchNearby"

FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.websiteUri",
    "places.regularOpeningHours",
    "places.nationalPhoneNumber",
    "places.primaryType",
    "places.location",
])

NOT_REAL_WEBSITE_DOMAINS = [
    "instagram.com",
    "facebook.com",
    "fb.com",
    "tiktok.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "linkedin.com",
    "t.me",
    "telegram.me",
    "wa.me",
    "whatsapp.com",
    "vk.com",
    "bolt.eu",
    "wolt.com",
    "glovo.com",
    "getir.com",
    "yemeksepeti.com",
    "trendyol.com",
]

_cache = {}
CACHE_TTL = 900


def _cache_key(latitude, longitude, category, radius):
    raw = f"{latitude:.4f}:{longitude:.4f}:{category}:{radius}"
    return hashlib.md5(raw.encode()).hexdigest()


def _clean_cache():
    now = time.time()
    expired = [k for k, v in _cache.items() if now - v["timestamp"] > CACHE_TTL]
    for k in expired:
        del _cache[k]


def _is_real_website(uri):
    if not uri:
        return False
    uri_lower = uri.lower()
    for domain in NOT_REAL_WEBSITE_DOMAINS:
        if domain in uri_lower:
            return False
    return True


def _format_place(place):
    return {
        "id": place.get("id"),
        "name": place.get("displayName", {}).get("text", ""),
        "address": place.get("formattedAddress", ""),
        "phone": place.get("nationalPhoneNumber", ""),
        "type": place.get("primaryType", ""),
        "location": place.get("location", {}),
        "opening_hours": _format_hours(place.get("regularOpeningHours")),
    }


def search_places_without_website(latitude, longitude, category, radius=2000, max_results=20):
    if category not in PLACE_CATEGORIES:
        return {"error": f"Invalid category: {category}"}

    _clean_cache()

    key = _cache_key(latitude, longitude, category, radius)
    if key in _cache:
        logger.info(f"Cache hit: {category} at ({latitude},{longitude})")
        return _cache[key]["data"]

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": settings.GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": FIELD_MASK,
    }

    body = {
        "includedTypes": [PLACE_CATEGORIES[category]],
        "maxResultCount": max_results,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "radius": radius,
            }
        },
    }

    try:
        response = requests.post(NEARBY_SEARCH_URL, json=body, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        logger.error(f"Google API timeout - lat:{latitude} lng:{longitude} cat:{category}")
        return {"error": "Google API timeout"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Google API error - {str(e)}")
        return {"error": "Search service is currently unavailable"}

    places = data.get("places", [])

    no_website = []
    with_website = []

    for place in places:
        website = place.get("websiteUri", "")
        formatted = _format_place(place)

        if not _is_real_website(website):
            formatted["social_only"] = bool(website)
            no_website.append(formatted)
        else:
            formatted["website"] = website
            with_website.append(formatted)

    no_website.sort(key=lambda x: (not bool(x.get("phone"))))

    result = {
        "results": no_website,
        "competitors": with_website[:5],
        "total_found": len(places),
        "without_website": len(no_website),
    }

    _cache[key] = {"data": result, "timestamp": time.time()}
    logger.info(f"Search: {category} at ({latitude},{longitude}) r={radius} - {len(no_website)}/{len(places)} without website")

    return result


def _format_hours(hours_data):
    if not hours_data:
        return None
    return hours_data.get("weekdayDescriptions", [])