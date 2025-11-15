from rest_framework import serializers

from healthy_herron.users.models import Profile, User


class UserSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ["name", "url"]

        extra_kwargs = {
            "url": {"view_name": "api:user-detail", "lookup_field": "pk"},
        }


class ProfileSerializer(serializers.ModelSerializer[Profile]):
    """Serializer for Profile model."""

    class Meta:
        model = Profile
        fields = ["user", "display_name", "avatar", "configuration", "created_at", "updated_at"]
        read_only_fields = ["user", "created_at", "updated_at"]


class ProfileUpdateSerializer(serializers.ModelSerializer[Profile]):
    """Serializer for Profile updates (excludes user field)."""

    class Meta:
        model = Profile
        fields = ["display_name", "avatar", "configuration"]


class ConfigurationSerializer(serializers.Serializer):
    """Serializer for configuration operations."""

    app_name = serializers.CharField(max_length=100)
    key = serializers.CharField(max_length=100)
    value = serializers.JSONField(required=False)  # Optional for DELETE operations
