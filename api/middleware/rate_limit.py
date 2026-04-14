import time
from django.http import JsonResponse


class RateLimitMiddleware:
    RATE_LIMITS = {
        "/api/search/": {"max_requests": 30, "window": 3600},
        "/api/search/area/": {"max_requests": 30, "window": 3600},
        "/api/chat/": {"max_requests": 30, "window": 3600},
    }

    def __init__(self, get_response):
        self.get_response = get_response
        self.requests_log = {}

    def __call__(self, request):
        path = request.path
        if path not in self.RATE_LIMITS:
            return self.get_response(request)

        ip = self._get_client_ip(request)
        key = f"{ip}:{path}"
        limit = self.RATE_LIMITS[path]
        now = time.time()

        if key in self.requests_log:
            self.requests_log[key] = [
                t for t in self.requests_log[key]
                if now - t < limit["window"]
            ]
        else:
            self.requests_log[key] = []

        if len(self.requests_log[key]) >= limit["max_requests"]:
            retry_after = int(limit["window"] - (now - self.requests_log[key][0]))
            return JsonResponse(
                {"error": "Too many requests. Try again later."},
                status=429,
                headers={"Retry-After": str(retry_after)},
            )

        self.requests_log[key].append(now)
        return self.get_response(request)

    def _get_client_ip(self, request):
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            return x_forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")