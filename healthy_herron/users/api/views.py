from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from healthy_herron.users.models import User

from .serializers import (
    ConfigurationSerializer,
    ProfileSerializer,
    ProfileUpdateSerializer,
    UserSerializer,
)


class UserViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = "pk"

    def get_queryset(self, *args, **kwargs):
        assert isinstance(self.request.user.id, int)
        return self.queryset.filter(id=self.request.user.id)

    @action(detail=False)
    def me(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)


class ProfileViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    """ViewSet for Profile management."""

    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        """Return the current user's profile."""
        return self.request.user.profile

    def get_serializer_class(self):
        """Use different serializer for updates."""
        if self.action in ["update", "partial_update"]:
            return ProfileUpdateSerializer
        return ProfileSerializer

    @action(detail=False, methods=["get"])
    def me(self, request):
        """Get current user's profile."""
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def set_configuration(self, request):
        """Set a configuration value."""
        serializer = ConfigurationSerializer(data=request.data)
        if serializer.is_valid():
            profile = self.get_object()
            app_name = serializer.validated_data["app_name"]
            key = serializer.validated_data["key"]
            value = serializer.validated_data["value"]

            profile.set_configuration(app_name, key, value)

            return Response(
                {
                    "message": "Configuration updated successfully",
                    "app_name": app_name,
                    "key": key,
                    "value": value,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["delete"])
    def delete_configuration(self, request):
        """Delete a configuration value."""
        serializer = ConfigurationSerializer(data=request.data)
        if serializer.is_valid():
            profile = self.get_object()
            app_name = serializer.validated_data["app_name"]
            key = serializer.validated_data.get("key")

            profile.delete_configuration(app_name, key)

            message = f"Configuration deleted successfully: {app_name}"
            if key:
                message += f".{key}"

            return Response(
                {
                    "message": message,
                },
                status=status.HTTP_204_NO_CONTENT,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
