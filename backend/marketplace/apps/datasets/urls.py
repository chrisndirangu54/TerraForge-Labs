from django.urls import path

from backend.marketplace.apps.datasets.views import index

urlpatterns = [path("", index)]
