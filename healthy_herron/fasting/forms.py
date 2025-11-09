from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Fast


class StartFastForm(forms.ModelForm):
    """Form for starting a new fast."""

    class Meta:
        model = Fast
        fields = ['start_time']
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                }
            )
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Set user on instance for validation
        if self.user:
            self.instance.user = self.user

        # Set default start time to now
        if not self.instance.pk and not self.initial.get('start_time'):
            from django.utils import timezone
            self.fields['start_time'].initial = timezone.now()

    def clean(self):
        """Validate that user doesn't have an active fast."""
        cleaned_data = super().clean()

        if self.user:
            # Check for existing active fast
            existing_active = Fast.objects.active_for_user(self.user)
            if existing_active.exists():
                raise ValidationError(
                    _("You already have an active fast. Please end your current fast before starting a new one.")
                )

        return cleaned_data

    def clean_start_time(self):
        """Validate that start time is not in the future."""
        start_time = self.cleaned_data.get('start_time')
        if start_time and start_time > timezone.now():
            self.add_error(
                'start_time',
                _("Start time cannot be in the future."),
            )
        return start_time

    def save(self, commit=True):
        """Save the fast with the current user."""
        fast = super().save(commit=False)
        if self.user:
            fast.user = self.user

        if commit:
            fast.save()
        return fast


class EndFastForm(forms.ModelForm):
    """Form for ending an active fast with emotional status and comments."""

    class Meta:
        model = Fast
        fields = ['end_time', 'emotional_status', 'comments']
        widgets = {
            'end_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                }
            ),
            'emotional_status': forms.Select(
                attrs={
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                }
            ),
            'comments': forms.Textarea(
                attrs={
                    'rows': 4,
                    'maxlength': 128,
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                    'placeholder': 'Share your thoughts about this fast (optional, max 128 characters)'
                }
            )
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Set default end time to now
        if not self.initial.get('end_time'):
            from django.utils import timezone
            self.fields['end_time'].initial = timezone.now()

        # Make emotional status required
        self.fields['emotional_status'].required = True

    def clean(self):
        """Validate end time requirements."""
        cleaned_data = super().clean()
        end_time = cleaned_data.get('end_time')
        emotional_status = cleaned_data.get('emotional_status')

        # Validate that emotional status is provided when ending
        if end_time and not emotional_status:
            raise ValidationError(
                _("Emotional status is required when ending a fast."),
                code='emotional_status_required',
            )

        # Validate that end time is after start time
        if self.instance and self.instance.start_time and end_time:
            if end_time <= self.instance.start_time:
                self.add_error('end_time', _("End time must be after the start time."))

        return cleaned_data


class FastUpdateForm(forms.ModelForm):
    """Form for updating an existing fast record."""

    class Meta:
        model = Fast
        fields = ['start_time', 'end_time', 'emotional_status', 'comments']
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                }
            ),
            'end_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                }
            ),
            'emotional_status': forms.Select(
                attrs={
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                }
            ),
            'comments': forms.Textarea(
                attrs={
                    'rows': 4,
                    'maxlength': 128,
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                    'placeholder': 'Share your thoughts about this fast (optional, max 128 characters)'
                }
            )
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Make end_time optional for active fasts
        self.fields['end_time'].required = False

        # Make emotional status required only if end_time is set
        self.fields['emotional_status'].required = False

    def clean(self):
        """Validate update requirements."""
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        emotional_status = cleaned_data.get('emotional_status')

        # Validate that end time is after start time if provided
        if start_time and end_time and end_time <= start_time:
            self.add_error("end_time", _("End time must be after the start time."))

        # Validate that emotional status is provided when ending
        if end_time and not emotional_status:
            raise ValidationError(
                _("Emotional status is required when setting an end time.")
            )

        return cleaned_data
