import json

import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory

from healthy_herron.users.api.views import ProfileViewSet, UserViewSet
from healthy_herron.users.models import User
from healthy_herron.users.tests.factories import UserFactory


class TestUserViewSet:
    @pytest.fixture
    def api_rf(self) -> APIRequestFactory:
        return APIRequestFactory()

    def test_get_queryset(self, user: User, api_rf: APIRequestFactory):
        view = UserViewSet()
        request = api_rf.get("/fake-url/")
        request.user = user

        view.request = request

        assert user in view.get_queryset()

    def test_me(self, user: User, api_rf: APIRequestFactory):
        view = UserViewSet()
        request = api_rf.get("/fake-url/")
        request.user = user

        view.request = request

        response = view.me(request)  # type: ignore[call-arg, arg-type, misc]

        assert response.data == {
            "url": f"http://testserver/api/users/{user.pk}/",
            "name": user.name,
        }


class TestProfileViewSet:
    @pytest.fixture
    def api_rf(self) -> APIRequestFactory:
        return APIRequestFactory()

    @pytest.mark.django_db
    def test_get_profile_me(self, api_rf: APIRequestFactory):
        """Test getting current user's profile."""
        user = UserFactory()
        profile = user.profile

        view = ProfileViewSet()
        view.action = "me"  # Set the action
        view.format_kwarg = None  # Set format_kwarg
        request = api_rf.get("/fake-url/")
        request.user = user  # Set user directly for testing
        view.request = request

        response = view.me(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["display_name"] == profile.display_name
        assert "configuration" in response.data
        assert "avatar" in response.data

    @pytest.mark.django_db
    def test_update_profile(self, api_rf: APIRequestFactory):
        """Test updating profile."""
        user = UserFactory()
        profile = user.profile

        view = ProfileViewSet()
        view.action = "partial_update"  # Set the action
        data = {
            "display_name": "Updated Name 🚀",
        }
        request = api_rf.patch("/fake-url/", data)
        request.user = user
        view.request = request
        view.format_kwarg = None

        response = view.partial_update(request)

        assert response.status_code == status.HTTP_200_OK
        profile.refresh_from_db()
        assert profile.display_name == "Updated Name 🚀"

    @pytest.mark.django_db
    def test_set_configuration(self, api_rf: APIRequestFactory):
        """Test setting configuration via API."""
        user = UserFactory()
        profile = user.profile

        view = ProfileViewSet()
        view.action = "set_configuration"  # Set the action
        data = {
            "app_name": "test_app",
            "key": "test_key",
            "value": "test_value",
        }
        request = api_rf.post(
            "/fake-url/",
            json.dumps(data),
            content_type="application/json",
        )
        request.user = user
        view.request = request
        view.format_kwarg = None

        response = view.set_configuration(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "Configuration updated successfully"

        profile.refresh_from_db()
        assert profile.get_configuration("test_app", "test_key") == "test_value"

    @pytest.mark.django_db
    def test_delete_configuration(self, api_rf: APIRequestFactory):
        """Test deleting configuration via API."""
        user = UserFactory()
        profile = user.profile
        profile.set_configuration("test_app", "test_key", "test_value")

        view = ProfileViewSet()
        view.action = "delete_configuration"  # Set the action
        data = {
            "app_name": "test_app",
            "key": "test_key",
        }
        request = api_rf.delete(
            "/fake-url/",
            json.dumps(data),
            content_type="application/json",
        )
        request.user = user
        view.request = request
        view.format_kwarg = None

        response = view.delete_configuration(request)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        profile.refresh_from_db()
        assert profile.get_configuration("test_app", "test_key") is None
