from collections.abc import Sequence
from typing import Any

from factory import Faker, post_generation
from factory.django import DjangoModelFactory

from healthy_herron.users.models import Profile, User


class UserFactory(DjangoModelFactory[User]):
    email = Faker("email")
    name = Faker("name")

    @post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):  # noqa: FBT001
        password = (
            extracted
            if extracted
            else Faker(
                "password",
                length=42,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            ).evaluate(None, None, extra={"locale": None})
        )
        self.set_password(password)

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        """Save again the instance if creating and at least one hook ran."""
        if create and results and not cls._meta.skip_postgeneration_save:
            # Some post-generation hooks ran, and may have modified us.
            instance.save()

    class Meta:
        model = User
        django_get_or_create = ["email"]


class ProfileFactory(DjangoModelFactory[Profile]):
    """Factory for creating Profile instances."""

    # Don't create a user automatically - use existing profile from signal or create manually
    display_name = Faker("name")

    class Meta:
        model = Profile
        exclude = ["user"]  # Don't auto-generate user field

    @classmethod
    def create(cls, **kwargs):
        """Override create to handle user creation properly."""
        if "user" not in kwargs:
            # Create a user which will auto-create a profile via signal
            user = UserFactory()
            # Get the auto-created profile
            profile = user.profile
            # Update it with any provided fields
            for key, value in kwargs.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            profile.save()
            return profile
        # User provided, create profile normally
        return super().create(**kwargs)
