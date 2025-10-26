# Quickstart Guide: Fasting Tracker App

**Date**: 2025-10-25  
**Branch**: `001-fasting-app`

## Overview

This guide provides step-by-step instructions for implementing the fasting tracker application according to the specification and constitution requirements.

## Prerequisites

- Django 5.2.7 project set up
- PostgreSQL configured
- Tailwind CSS configured
- pytest and FactoryBoy available
- User authentication system working

## Installation Steps

### 1. Install Dependencies

Add django-guardian to the project dependencies:

```bash
# Add to pyproject.toml [tool.uv.dependencies]
django-guardian = "^2.4.0"

# Install the dependency
uv add django-guardian
```

### 2. Update Django Settings

Add to `config/settings/base.py`:

```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... existing apps
    'guardian',
    'healthy_herron.fasting',
]

# Add authentication backend for django-guardian
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
]

# Guardian settings
GUARDIAN_RAISE_403 = True
GUARDIAN_RENDER_403 = True
```

### 3. Create the Fasting App

```bash
# Create the Django app
cd healthy_herron
python ../manage.py startapp fasting

# Create required directories
mkdir -p fasting/api
mkdir -p fasting/tests
mkdir -p templates/fasting
mkdir -p static/js/fasting
```

### 4. Implement the Fast Model

Create `healthy_herron/fasting/models.py`:

```python
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone
from model_utils.models import TimeStampedModel
from healthy_herron.core.models import AuditableModel


class FastManager(models.Manager):
    """Custom manager for Fast model with user filtering."""
    
    def for_user(self, user):
        """Return fasts for a specific user."""
        return self.filter(user=user)
    
    def active_for_user(self, user):
        """Return active (unfinished) fasts for a user."""
        return self.filter(user=user, end_time__isnull=True)
    
    def completed_for_user(self, user):
        """Return completed fasts for a user."""
        return self.filter(user=user, end_time__isnull=False)


class Fast(AuditableModel, TimeStampedModel):
    """Model representing a fasting period."""
    
    EMOTIONAL_STATUS_CHOICES = [
        ('energized', 'Energized'),
        ('satisfied', 'Satisfied'),
        ('challenging', 'Challenging'),
        ('difficult', 'Difficult'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='fasts',
        db_index=True
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    emotional_status = models.CharField(
        max_length=20,
        choices=EMOTIONAL_STATUS_CHOICES,
        null=True,
        blank=True
    )
    comments = models.TextField(max_length=128, blank=True)
    
    objects = FastManager()
    
    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['user', '-start_time']),
            models.Index(fields=['user', 'end_time']),
        ]
        permissions = [
            ('view_own_fast', 'Can view own fasting records'),
            ('change_own_fast', 'Can change own fasting records'),
            ('delete_own_fast', 'Can delete own fasting records'),
        ]
    
    def clean(self):
        """Model validation."""
        super().clean()
        
        # Validate end_time is after start_time
        if self.end_time and self.start_time and self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time")
        
        # Validate emotional_status is provided when ending fast
        if self.end_time and not self.emotional_status:
            raise ValidationError("Emotional status is required when ending a fast")
        
        # Validate no multiple active fasts for same user
        if not self.end_time:  # Active fast
            existing_active = Fast.objects.filter(
                user=self.user,
                end_time__isnull=True
            ).exclude(pk=self.pk)
            if existing_active.exists():
                raise ValidationError("User can only have one active fast at a time")
    
    @property
    def is_active(self):
        """Return True if fast is ongoing."""
        return self.end_time is None
    
    @property
    def duration(self):
        """Calculate duration for completed fasts."""
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def elapsed_time(self):
        """Calculate elapsed time from start to now."""
        return timezone.now() - self.start_time
    
    @property
    def duration_hours(self):
        """Human-readable duration for completed fasts."""
        if self.duration:
            total_seconds = int(self.duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        return None
    
    @property
    def elapsed_hours(self):
        """Human-readable elapsed time."""
        total_seconds = int(self.elapsed_time.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    
    def end_fast(self, emotional_status, comments=''):
        """Complete the fast with emotional status."""
        self.end_time = timezone.now()
        self.emotional_status = emotional_status
        self.comments = comments
        self.full_clean()
        self.save()
    
    def get_absolute_url(self):
        """URL to fast detail view."""
        return reverse('fasting:fast_detail', kwargs={'pk': self.pk})
    
    def __str__(self):
        status = "Active" if self.is_active else "Completed"
        return f"Fast by {self.user.username} - {status} ({self.start_time.date()})"
```

### 5. Create Database Migration

```bash
python manage.py makemigrations fasting
python manage.py migrate
```

### 6. Set Up Guardian Permissions

Create `healthy_herron/fasting/signals.py`:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm
from .models import Fast


@receiver(post_save, sender=Fast)
def assign_fast_permissions(sender, instance, created, **kwargs):
    """Assign object-level permissions to fast owner."""
    if created:
        assign_perm('view_fast', instance.user, instance)
        assign_perm('change_fast', instance.user, instance)
        assign_perm('delete_fast', instance.user, instance)
```

Update `healthy_herron/fasting/apps.py`:

```python
from django.apps import AppConfig


class FastingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'healthy_herron.fasting'
    
    def ready(self):
        import healthy_herron.fasting.signals
```

### 7. Create URL Configuration

Create `healthy_herron/fasting/urls.py`:

```python
from django.urls import path, include
from . import views

app_name = 'fasting'

urlpatterns = [
    path('', views.FastListView.as_view(), name='fast_list'),
    path('start/', views.FastCreateView.as_view(), name='fast_start'),
    path('<int:pk>/', views.FastDetailView.as_view(), name='fast_detail'),
    path('<int:pk>/edit/', views.FastUpdateView.as_view(), name='fast_edit'),
    path('<int:pk>/delete/', views.FastDeleteView.as_view(), name='fast_delete'),
    path('<int:pk>/end/', views.FastEndView.as_view(), name='fast_end'),
    path('api/', include('healthy_herron.fasting.api.urls')),
]
```

Add to main `config/urls.py`:

```python
urlpatterns = [
    # ... existing patterns
    path('fasting/', include('healthy_herron.fasting.urls')),
]
```

### 8. Create View Classes

Create `healthy_herron/fasting/views.py`:

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from guardian.mixins import PermissionRequiredMixin
from .models import Fast
from .forms import FastForm, FastEndForm


class FastPermissionMixin(PermissionRequiredMixin):
    """Mixin for object-level permissions on Fast objects."""
    
    def get_object(self):
        """Override to ensure user can only access their own fasts."""
        obj = get_object_or_404(Fast, pk=self.kwargs['pk'], user=self.request.user)
        return obj


class FastListView(LoginRequiredMixin, ListView):
    """Display user's fasting history."""
    model = Fast
    template_name = 'fasting/fast_list.html'
    context_object_name = 'fasts'
    paginate_by = 20
    
    def get_queryset(self):
        return Fast.objects.for_user(self.request.user)


class FastDetailView(LoginRequiredMixin, FastPermissionMixin, DetailView):
    """Display detailed view of a fast with real-time updates."""
    model = Fast
    template_name = 'fasting/fast_detail.html'
    permission_required = 'fasting.view_fast'


class FastCreateView(LoginRequiredMixin, CreateView):
    """Start a new fast."""
    model = Fast
    form_class = FastForm
    template_name = 'fasting/fast_form.html'
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.start_time = timezone.now()
        return super().form_valid(form)


class FastUpdateView(LoginRequiredMixin, FastPermissionMixin, UpdateView):
    """Edit fast details."""
    model = Fast
    form_class = FastForm
    template_name = 'fasting/fast_form.html'
    permission_required = 'fasting.change_fast'


class FastDeleteView(LoginRequiredMixin, FastPermissionMixin, DeleteView):
    """Delete a fast record."""
    model = Fast
    template_name = 'fasting/fast_confirm_delete.html'
    success_url = reverse_lazy('fasting:fast_list')
    permission_required = 'fasting.delete_fast'


class FastEndView(LoginRequiredMixin, FastPermissionMixin, UpdateView):
    """End an active fast with emotional status."""
    model = Fast
    form_class = FastEndForm
    template_name = 'fasting/fast_end.html'
    permission_required = 'fasting.change_fast'
    
    def form_valid(self, form):
        form.instance.end_time = timezone.now()
        return super().form_valid(form)
```

### 9. Create Forms

Create `healthy_herron/fasting/forms.py`:

```python
from django import forms
from .models import Fast


class FastForm(forms.ModelForm):
    """Form for creating and editing fasts."""
    
    class Meta:
        model = Fast
        fields = ['start_time', 'end_time', 'emotional_status', 'comments']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'emotional_status': forms.RadioSelect(),
            'comments': forms.Textarea(attrs={'rows': 3, 'maxlength': 128}),
        }


class FastEndForm(forms.ModelForm):
    """Form for ending an active fast."""
    
    class Meta:
        model = Fast
        fields = ['emotional_status', 'comments']
        widgets = {
            'emotional_status': forms.RadioSelect(),
            'comments': forms.Textarea(attrs={'rows': 3, 'maxlength': 128}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['emotional_status'].required = True
```

### 10. Create API Endpoints

Create `healthy_herron/fasting/api/serializers.py`:

```python
from rest_framework import serializers
from ..models import Fast


class FastSerializer(serializers.ModelSerializer):
    """Serializer for Fast model."""
    is_active = serializers.ReadOnlyField()
    duration_hours = serializers.ReadOnlyField()
    elapsed_hours = serializers.ReadOnlyField()
    
    class Meta:
        model = Fast
        fields = [
            'id', 'start_time', 'end_time', 'emotional_status', 'comments',
            'is_active', 'duration_hours', 'elapsed_hours', 'created', 'modified'
        ]
        read_only_fields = ['created', 'modified']
    
    def validate(self, data):
        """Cross-field validation."""
        if data.get('end_time') and data.get('start_time'):
            if data['end_time'] <= data['start_time']:
                raise serializers.ValidationError("End time must be after start time")
        
        if data.get('end_time') and not data.get('emotional_status'):
            raise serializers.ValidationError("Emotional status is required when ending a fast")
        
        return data
```

Create `healthy_herron/fasting/api/views.py`:

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from ..models import Fast
from .serializers import FastSerializer


class FastViewSet(viewsets.ModelViewSet):
    """API ViewSet for Fast model."""
    serializer_class = FastSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only user's own fasts."""
        return Fast.objects.for_user(self.request.user)
    
    def perform_create(self, serializer):
        """Set user and default start time when creating fast."""
        serializer.save(
            user=self.request.user,
            start_time=serializer.validated_data.get('start_time', timezone.now())
        )
    
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """End an active fast with emotional status."""
        fast = self.get_object()
        
        if fast.end_time:
            return Response(
                {'detail': 'Fast is already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        emotional_status = request.data.get('emotional_status')
        if not emotional_status:
            return Response(
                {'detail': 'Emotional status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        fast.end_fast(
            emotional_status=emotional_status,
            comments=request.data.get('comments', '')
        )
        
        serializer = self.get_serializer(fast)
        return Response(serializer.data)
```

Create `healthy_herron/fasting/api/urls.py`:

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FastViewSet

router = DefaultRouter()
router.register(r'fasts', FastViewSet, basename='fast')

urlpatterns = [
    path('', include(router.urls)),
]
```

### 11. Create Templates

Create basic templates in `healthy_herron/templates/fasting/`:

```html
<!-- base.html -->
{% extends "base.html" %}

{% block title %}Fasting Tracker{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    {% block fasting_content %}
    {% endblock %}
</div>
{% endblock %}

<!-- fast_list.html -->
{% extends "fasting/base.html" %}

{% block fasting_content %}
<div class="max-w-4xl mx-auto">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-bold">Your Fasting History</h1>
        <a href="{% url 'fasting:fast_start' %}" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
            Start New Fast
        </a>
    </div>
    
    <!-- Fast list implementation -->
    {% for fast in fasts %}
        <div class="bg-white shadow rounded-lg p-6 mb-4">
            <!-- Fast details -->
        </div>
    {% empty %}
        <p class="text-gray-500">No fasting records yet. Start your first fast!</p>
    {% endfor %}
</div>
{% endblock %}
```

### 12. Create Real-time JavaScript

Create `healthy_herron/static/js/fasting/realtime-updates.js`:

```javascript
class FastingTimer {
    constructor(startTime, elementId) {
        this.startTime = new Date(startTime);
        this.element = document.getElementById(elementId);
        this.intervalId = null;
    }
    
    start() {
        this.update();
        this.intervalId = setInterval(() => this.update(), 15000);
    }
    
    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }
    
    update() {
        const now = new Date();
        const elapsed = now - this.startTime;
        const hours = Math.floor(elapsed / (1000 * 60 * 60));
        const minutes = Math.floor((elapsed % (1000 * 60 * 60)) / (1000 * 60));
        
        if (this.element) {
            this.element.textContent = `${hours}h ${minutes}m`;
        }
    }
}

// Initialize timer when page loads
document.addEventListener('DOMContentLoaded', function() {
    const timerElement = document.getElementById('elapsed-time');
    const startTimeElement = document.getElementById('start-time');
    
    if (timerElement && startTimeElement) {
        const startTime = startTimeElement.getAttribute('data-start-time');
        const timer = new FastingTimer(startTime, 'elapsed-time');
        timer.start();
        
        // Stop timer when page is hidden
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                timer.stop();
            } else {
                timer.start();
            }
        });
    }
});
```

### 13. Create Tests

Create test factories in `healthy_herron/fasting/tests/factories.py`:

```python
import factory
from django.contrib.auth.models import User
from guardian.shortcuts import assign_perm
from ..models import Fast


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")


class FastFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Fast
    
    user = factory.SubFactory(UserFactory)
    start_time = factory.Faker('date_time_this_month')
    end_time = None
    emotional_status = None
    comments = factory.Faker('text', max_nb_chars=100)
    
    @factory.post_generation
    def assign_permissions(obj, create, extracted, **kwargs):
        if create:
            assign_perm('view_fast', obj.user, obj)
            assign_perm('change_fast', obj.user, obj)
            assign_perm('delete_fast', obj.user, obj)


class CompletedFastFactory(FastFactory):
    end_time = factory.Faker('date_time_this_month')
    emotional_status = factory.Iterator(['energized', 'satisfied', 'challenging', 'difficult'])
```

### 14. Run Tests

```bash
python manage.py test healthy_herron.fasting
```

### 15. Add to URL Configuration

Update the main URL configuration to include the fasting app URLs.

## Development Workflow

1. **Create branch**: `git checkout -b 001-fasting-app`
2. **Implement feature**: Follow the steps above
3. **Write tests**: Ensure comprehensive test coverage
4. **Test manually**: Verify all user stories work correctly
5. **Submit for review**: Create pull request to main branch

## Verification Checklist

- [ ] All functional requirements (FR-001 through FR-022) implemented
- [ ] Object-level permissions working with django-guardian
- [ ] Real-time updates working every 15 seconds
- [ ] Responsive design with Tailwind CSS
- [ ] All tests passing
- [ ] API endpoints documented and tested
- [ ] Templates in correct fasting/templates directory
- [ ] Performance requirements met

This quickstart provides a complete implementation foundation for the fasting tracker app following all specifications and constitution requirements.