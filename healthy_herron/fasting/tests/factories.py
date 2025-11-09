import factory
from django.utils import timezone

from healthy_herron.fasting.models import Fast
from healthy_herron.users.tests.factories import UserFactory


class FastFactory(factory.django.DjangoModelFactory):
    """Factory for creating Fast instances for testing."""

    class Meta:
        model = Fast

    user = factory.SubFactory(UserFactory)
    start_time = factory.LazyFunction(timezone.now)
    end_time = None  # Default to active fast
    emotional_status = None
    comments = factory.Faker("text", max_nb_chars=128)

    @factory.post_generation
    def completed(obj, create, extracted, **kwargs):
        """Create a completed fast if completed=True is passed."""
        if extracted:
            obj.end_time = obj.start_time + timezone.timedelta(hours=16)
            obj.emotional_status = factory.Faker("random_element",
                                               elements=["energized", "satisfied", "challenging", "difficult"]).generate({})
            if create:
                obj.save()


class ActiveFastFactory(FastFactory):
    """Factory for creating active (ongoing) fasts."""
    end_time = None
    emotional_status = None
    comments = ""


class CompletedFastFactory(FastFactory):
    """Factory for creating completed fasts."""
    end_time = factory.LazyAttribute(lambda obj: obj.start_time + timezone.timedelta(hours=16))
    emotional_status = factory.Faker("random_element",
                                   elements=["energized", "satisfied", "challenging", "difficult"])
    comments = factory.Faker("text", max_nb_chars=100)
