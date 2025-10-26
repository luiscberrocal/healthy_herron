import factory
from django.contrib.auth import get_user_model
from django.utils import timezone

from healthy_herron.fasting.models import Fast

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating User instances for testing."""
    
    class Meta:
        model = User
        django_get_or_create = ('username',)
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')


class FastFactory(factory.django.DjangoModelFactory):
    """Factory for creating Fast instances for testing."""
    
    class Meta:
        model = Fast
    
    user = factory.SubFactory(UserFactory)
    start_time = factory.LazyFunction(timezone.now)
    end_time = None  # Default to active fast
    emotional_status = None
    comments = factory.Faker('text', max_nb_chars=128)
    
    @factory.post_generation
    def completed(obj, create, extracted, **kwargs):
        """Create a completed fast if completed=True is passed."""
        if extracted:
            obj.end_time = obj.start_time + timezone.timedelta(hours=16)
            obj.emotional_status = factory.Faker('random_element', 
                                               elements=['energized', 'satisfied', 'challenging', 'difficult']).generate({})
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
    emotional_status = factory.Faker('random_element', 
                                   elements=['energized', 'satisfied', 'challenging', 'difficult'])
    comments = factory.Faker('text', max_nb_chars=100)