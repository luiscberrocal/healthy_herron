import pytest
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile

from healthy_herron.users.models import Profile, User
from healthy_herron.users.tests.factories import ProfileFactory, UserFactory


def test_user_get_absolute_url(user: User):
    assert user.get_absolute_url() == f"/users/{user.pk}/"


class TestProfile:
    """Tests for the Profile model."""

    @pytest.mark.django_db
    def test_profile_auto_creation_on_user_creation(self):
        """Test that a Profile is automatically created when a User is created."""
        user = UserFactory()

        # Profile should be auto-created
        assert hasattr(user, "profile")
        profile = user.profile

        # Check profile attributes
        assert profile.user == user
        assert profile.display_name == user.name or user.email.split("@")[0]
        assert profile.configuration == {
            "fasting": {
                "min_fast_duration": 30,
                "max_fast_duration": 1440,
            },
        }

    @pytest.mark.django_db
    def test_profile_str_representation(self):
        """Test the string representation of Profile."""
        user = UserFactory(email="test@example.com", name="Test User")
        profile = user.profile

        assert str(profile) == "test@example.com - Test User"

    @pytest.mark.django_db
    def test_profile_default_configuration(self):
        """Test that Profile gets default configuration."""
        profile = ProfileFactory()

        expected_config = {
            "fasting": {
                "min_fast_duration": 30,
                "max_fast_duration": 1440,
            },
        }
        assert profile.configuration == expected_config

    @pytest.mark.django_db
    def test_profile_delete_cleans_avatar(self):
        """Test that avatar file is deleted when profile is deleted."""
        # Create a simple image file
        image_content = b"fake-image-content"
        image_file = SimpleUploadedFile(
            "test.jpg",
            image_content,
            content_type="image/jpeg",
        )

        profile = ProfileFactory(avatar=image_file)
        avatar_path = profile.avatar.name

        # Verify file exists
        assert default_storage.exists(avatar_path)

        # Delete profile
        profile.delete()

        # Verify file is cleaned up
        assert not default_storage.exists(avatar_path)

    @pytest.mark.django_db
    def test_profile_avatar_replacement_cleans_old_file(self):
        """Test that old avatar file is deleted when replaced."""
        # Create first image
        image1 = SimpleUploadedFile(
            "test1.jpg",
            b"fake-image-1",
            content_type="image/jpeg",
        )
        profile = ProfileFactory(avatar=image1)
        old_avatar_path = profile.avatar.name

        # Create second image
        image2 = SimpleUploadedFile(
            "test2.jpg",
            b"fake-image-2",
            content_type="image/jpeg",
        )

        # Replace avatar
        profile.avatar = image2
        profile.save()

        # Old file should be deleted, new file should exist
        assert not default_storage.exists(old_avatar_path)
        assert default_storage.exists(profile.avatar.name)

        # Cleanup
        profile.delete()

    @pytest.mark.django_db
    def test_user_deletion_cleans_profile_and_avatar(self):
        """Test that user deletion triggers profile and avatar cleanup."""
        # Create user with profile and avatar
        image_content = b"fake-image-content"
        image_file = SimpleUploadedFile(
            "test.jpg",
            image_content,
            content_type="image/jpeg",
        )

        user = UserFactory()
        profile = user.profile
        profile.avatar = image_file
        profile.save()

        avatar_path = profile.avatar.name

        # Verify file exists
        assert default_storage.exists(avatar_path)

        # Delete user (should trigger profile deletion via CASCADE and signal cleanup)
        user.delete()

        # Verify file is cleaned up
        assert not default_storage.exists(avatar_path)

        # Verify profile is deleted
        assert not Profile.objects.filter(pk=profile.pk).exists()

    @pytest.mark.django_db
    def test_display_name_supports_emojis(self):
        """Test that display_name field properly supports emojis and Unicode."""
        emoji_name = "Test User 🚀 💯 🎉"
        unicode_name = "用户测试 🌟"

        # Test with emoji name
        profile1 = ProfileFactory(display_name=emoji_name)
        profile1.refresh_from_db()
        assert profile1.display_name == emoji_name

        # Test with Unicode characters
        profile2 = ProfileFactory(display_name=unicode_name)
        profile2.refresh_from_db()
        assert profile2.display_name == unicode_name

        # Test mixed content
        mixed_name = "Hello 世界 🌍 Test"
        profile3 = ProfileFactory(display_name=mixed_name)
        profile3.refresh_from_db()
        assert profile3.display_name == mixed_name

    @pytest.mark.django_db
    def test_avatar_valid_formats(self):
        """Test that valid avatar formats (JPEG, PNG) are accepted."""
        import io

        from PIL import Image

        # Create a valid JPEG
        jpeg_image = Image.new("RGB", (100, 100), color="red")
        jpeg_buffer = io.BytesIO()
        jpeg_image.save(jpeg_buffer, format="JPEG")
        jpeg_buffer.seek(0)

        jpeg_file = SimpleUploadedFile(
            "test.jpg",
            jpeg_buffer.getvalue(),
            content_type="image/jpeg",
        )

        # Create a valid PNG
        png_image = Image.new("RGBA", (100, 100), color="blue")
        png_buffer = io.BytesIO()
        png_image.save(png_buffer, format="PNG")
        png_buffer.seek(0)

        png_file = SimpleUploadedFile(
            "test.png",
            png_buffer.getvalue(),
            content_type="image/png",
        )

        # Test JPEG upload
        profile1 = ProfileFactory(avatar=jpeg_file)
        assert profile1.avatar is not None

        # Test PNG upload
        profile2 = ProfileFactory(avatar=png_file)
        assert profile2.avatar is not None

        # Cleanup
        profile1.delete()
        profile2.delete()

    @pytest.mark.django_db
    def test_avatar_size_validation(self):
        """Test that avatar size validation works (≤2MB)."""
        import io

        from PIL import Image

        # Create a large image (should exceed 2MB when saved)
        large_image = Image.new("RGB", (5000, 5000), color="red")
        large_buffer = io.BytesIO()
        large_image.save(large_buffer, format="JPEG", quality=95)
        large_buffer.seek(0)

        # This should be larger than 2MB
        large_file = SimpleUploadedFile(
            "large.jpg",
            large_buffer.getvalue(),
            content_type="image/jpeg",
        )

        # Test that validation error is raised for large file
        from django.core.exceptions import ValidationError

        from healthy_herron.users.models import validate_avatar_size

        with pytest.raises(ValidationError):
            validate_avatar_size(large_file)

    @pytest.mark.django_db
    def test_avatar_format_validation(self):
        """Test that avatar format validation works (JPEG/PNG only)."""
        # Create a non-image file
        text_file = SimpleUploadedFile(
            "test.txt",
            b"This is not an image",
            content_type="text/plain",
        )

        # Test that validation error is raised for non-image file
        from django.core.exceptions import ValidationError

        from healthy_herron.users.models import validate_avatar_format

        with pytest.raises(ValidationError):
            validate_avatar_format(text_file)

    @pytest.mark.django_db
    def test_set_configuration(self):
        """Test setting configuration values."""
        profile = ProfileFactory()

        # Test setting configuration for new app
        profile.set_configuration("testing", "param1", "value1")
        assert profile.configuration["testing"]["param1"] == "value1"

        # Test setting additional configuration for same app
        profile.set_configuration("testing", "param2", 42)
        assert profile.configuration["testing"]["param1"] == "value1"
        assert profile.configuration["testing"]["param2"] == 42

        # Test setting configuration for different app
        profile.set_configuration("another_app", "setting", True)
        assert profile.configuration["another_app"]["setting"] is True

        # Test overwriting existing value
        profile.set_configuration("testing", "param1", "new_value")
        assert profile.configuration["testing"]["param1"] == "new_value"

        # Verify changes are persisted
        profile.refresh_from_db()
        assert profile.configuration["testing"]["param1"] == "new_value"
        assert profile.configuration["testing"]["param2"] == 42
        assert profile.configuration["another_app"]["setting"] is True

    @pytest.mark.django_db
    def test_get_configuration(self):
        """Test getting configuration values."""
        profile = ProfileFactory()

        # Set some test data
        profile.set_configuration("test_app", "string_value", "hello")
        profile.set_configuration("test_app", "number_value", 123)
        profile.set_configuration("test_app", "bool_value", False)

        # Test getting specific values
        assert profile.get_configuration("test_app", "string_value") == "hello"
        assert profile.get_configuration("test_app", "number_value") == 123
        assert profile.get_configuration("test_app", "bool_value") is False

        # Test getting entire app configuration
        app_config = profile.get_configuration("test_app")
        assert app_config == {
            "string_value": "hello",
            "number_value": 123,
            "bool_value": False,
        }

        # Test getting non-existent values
        assert profile.get_configuration("test_app", "missing_key") is None
        assert (
            profile.get_configuration("test_app", "missing_key", "default") == "default"
        )
        assert profile.get_configuration("missing_app", "any_key") is None
        assert (
            profile.get_configuration("missing_app", "any_key", "default") == "default"
        )

    @pytest.mark.django_db
    def test_delete_configuration(self):
        """Test deleting configuration values."""
        profile = ProfileFactory()

        # Set up test data
        profile.set_configuration("app1", "key1", "value1")
        profile.set_configuration("app1", "key2", "value2")
        profile.set_configuration("app2", "key1", "value3")

        # Test deleting specific key
        profile.delete_configuration("app1", "key1")
        assert profile.get_configuration("app1", "key1") is None
        assert profile.get_configuration("app1", "key2") == "value2"
        assert profile.get_configuration("app2", "key1") == "value3"

        # Test deleting entire app configuration
        profile.delete_configuration("app1")
        assert profile.get_configuration("app1") is None
        assert profile.get_configuration("app2", "key1") == "value3"

        # Test deleting non-existent configuration (should not raise error)
        profile.delete_configuration("non_existent_app")
        profile.delete_configuration("app2", "non_existent_key")

        # Verify changes are persisted
        profile.refresh_from_db()
        assert profile.get_configuration("app1") is None
        assert profile.get_configuration("app2", "key1") == "value3"

    @pytest.mark.django_db
    def test_configuration_edge_cases(self):
        """Test edge cases for configuration management."""
        profile = ProfileFactory()

        # Test setting configuration on profile with empty configuration
        profile.configuration = None
        profile.set_configuration("test", "key", "value")
        assert profile.configuration == {"test": {"key": "value"}}

        # Test complex nested values
        complex_value = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "bool": True,
            "null": None,
        }
        profile.set_configuration("complex_app", "complex_config", complex_value)
        retrieved = profile.get_configuration("complex_app", "complex_config")
        assert retrieved == complex_value

        # Test deleting last key in app removes app entirely
        profile.set_configuration("temp_app", "only_key", "value")
        assert "temp_app" in profile.configuration
        profile.delete_configuration("temp_app", "only_key")
        assert "temp_app" not in profile.configuration
