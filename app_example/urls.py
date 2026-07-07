from django.urls import path

from app_example.views import notify

app_name = "app_example"

urlpatterns = [
    path("notify/", notify, name="notify"),
]
