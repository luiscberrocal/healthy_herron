"""API URLs for users app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "users_api"

router = DefaultRouter()
router.register("users", views.UserViewSet)
router.register("profile", views.ProfileViewSet, basename="profile")

urlpatterns = [
    path("", include(router.urls)),
]
