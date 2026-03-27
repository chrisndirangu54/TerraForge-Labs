from django.http import JsonResponse


def index(_request):
    return JsonResponse({"service": "marketplace", "status": "ok", "mode": "phase0"})
