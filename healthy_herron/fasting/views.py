import csv
import json
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)
from guardian.mixins import PermissionRequiredMixin

from .forms import EndFastForm, FastUpdateForm, StartFastForm
from .models import Fast, SessionManager


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard showing active fast status and timer."""

    template_name = "fasting/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get active fast for user
        active_fast = SessionManager.get_user_active_fast(self.request)
        context["active_fast"] = active_fast

        # Get recent completed fasts
        recent_fasts = Fast.objects.completed_for_user(self.request.user)[:5]
        context["recent_fasts"] = recent_fasts

        return context


class StartFastView(LoginRequiredMixin, CreateView):
    """View for starting a new fast."""

    model = Fast
    form_class = StartFastForm
    template_name = "fasting/start_fast.html"
    success_url = reverse_lazy("fasting:dashboard")

    def get_form_kwargs(self):
        """Pass current user to form."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Handle successful form submission."""
        response = super().form_valid(form)

        # Set active fast in session
        SessionManager.set_active_fast(self.request, self.object)

        messages.success(
            self.request,
            _("Fast started successfully! Your fasting timer is now running."),
        )

        return response

    def form_invalid(self, form):
        """Handle form validation errors."""
        messages.error(
            self.request,
            _(
                "There was an error starting your fast. Please check the form and try again.",
            ),
        )
        return super().form_invalid(form)


class EndFastView(LoginRequiredMixin, UpdateView):
    """View for ending an active fast with emotional status and comments."""

    model = Fast
    form_class = EndFastForm
    template_name = "fasting/end_fast.html"
    success_url = reverse_lazy("fasting:dashboard")

    def get_object(self):
        """Get the user's active fast."""
        active_fast = SessionManager.get_user_active_fast(self.request)
        if not active_fast:
            messages.error(self.request, _("You don't have an active fast to end."))
            msg = "No active fast found"
            raise Http404(msg)
        return active_fast

    def get_form_kwargs(self):
        """Pass current user to form."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Handle successful form submission with concurrency locking."""
        try:
            with transaction.atomic():
                # Lock the fast record to prevent concurrent modifications
                fast = Fast.objects.select_for_update().get(pk=self.object.pk)

                # Double-check that fast is still active
                if fast.end_time is not None:
                    messages.error(self.request, _("This fast has already been ended."))
                    return redirect("fasting:dashboard")

                # Save the form
                response = super().form_valid(form)

                # Clear active fast from session
                SessionManager.clear_active_fast(self.request)

                messages.success(
                    self.request,
                    _("Fast completed successfully! Duration: {}").format(
                        self.object.duration_hours,
                    ),
                )

                return response

        except Fast.DoesNotExist:
            messages.error(
                self.request, _("The fast you're trying to end no longer exists."),
            )
            return redirect("fasting:dashboard")

    def form_invalid(self, form):
        """Handle form validation errors."""
        messages.error(
            self.request,
            _(
                "There was an error ending your fast. Please check the form and try again.",
            ),
        )
        return super().form_invalid(form)


class FastTimerView(LoginRequiredMixin, TemplateView):
    """HTMX endpoint for real-time timer updates."""

    template_name = "fasting/timer_fragment.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get active fast for user
        active_fast = SessionManager.get_user_active_fast(self.request)
        context["active_fast"] = active_fast

        return context


class FastListView(LoginRequiredMixin, ListView):
    """View for displaying user's fasting history with pagination."""

    model = Fast
    template_name = "fasting/fast_list.html"
    context_object_name = "fasts"
    paginate_by = 20

    def get_queryset(self):
        """Return only user's fasts, ordered by most recent first."""
        return Fast.objects.filter(user=self.request.user).order_by("-start_time")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add summary statistics
        user_fasts = self.get_queryset()
        context["total_fasts"] = user_fasts.count()
        context["completed_fasts"] = user_fasts.filter(end_time__isnull=False).count()
        context["active_fasts"] = user_fasts.filter(end_time__isnull=True).count()

        return context


class FastDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """View for displaying detailed information about a specific fast."""

    model = Fast
    template_name = "fasting/fast_detail.html"
    context_object_name = "fast"
    permission_required = "fasting.view_own_fast"

    def get_object(self):
        """Get fast and verify user ownership."""
        fast = get_object_or_404(Fast, pk=self.kwargs["pk"])

        # Verify user owns this fast
        if fast.user != self.request.user:
            msg = "Fast not found"
            raise Http404(msg)

        return fast

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add navigation context
        user_fasts = Fast.objects.filter(user=self.request.user).order_by("-start_time")
        current_fast = self.object

        # Find previous and next fasts
        try:
            current_index = list(user_fasts.values_list("pk", flat=True)).index(
                current_fast.pk,
            )
            if current_index > 0:
                context["next_fast"] = user_fasts[current_index - 1]
            if current_index < user_fasts.count() - 1:
                context["previous_fast"] = user_fasts[current_index + 1]
        except (ValueError, IndexError):
            pass

        return context


class FastUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """View for updating an existing fast record."""

    model = Fast
    form_class = FastUpdateForm
    template_name = "fasting/fast_form.html"
    permission_required = "fasting.change_own_fast"

    def get_object(self):
        """Get fast and verify user ownership."""
        fast = get_object_or_404(Fast, pk=self.kwargs["pk"])

        # Verify user owns this fast
        if fast.user != self.request.user:
            msg = "Fast not found"
            raise Http404(msg)

        return fast

    def get_form_kwargs(self):
        """Pass current user to form."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Handle successful form submission."""
        try:
            with transaction.atomic():
                # Lock the fast record to prevent concurrent modifications
                Fast.objects.select_for_update().get(pk=self.object.pk)

                # Save the form
                response = super().form_valid(form)

                messages.success(self.request, _("Fast updated successfully!"))

                return response

        except Fast.DoesNotExist:
            messages.error(
                self.request, _("The fast you're trying to update no longer exists."),
            )
            return redirect("fasting:fast_list")

    def form_invalid(self, form):
        """Handle form validation errors."""
        messages.error(
            self.request,
            _(
                "There was an error updating your fast. Please check the form and try again.",
            ),
        )
        return super().form_invalid(form)

    def get_success_url(self):
        """Redirect to fast detail after successful update."""
        return reverse_lazy("fasting:fast_detail", kwargs={"pk": self.object.pk})


class FastDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """View for deleting a fast record with confirmation."""

    model = Fast
    template_name = "fasting/fast_confirm_delete.html"
    success_url = reverse_lazy("fasting:fast_list")
    permission_required = "fasting.delete_own_fast"

    def get_object(self):
        """Get fast and verify user ownership."""
        fast = get_object_or_404(Fast, pk=self.kwargs["pk"])

        # Verify user owns this fast
        if fast.user != self.request.user:
            msg = "Fast not found"
            raise Http404(msg)

        return fast

    def delete(self, request, *args, **kwargs):
        """Handle fast deletion."""
        self.object = self.get_object()

        # If this is an active fast, clear it from session
        if self.object.is_active:
            SessionManager.clear_active_fast(request)

        messages.success(request, _("Fast deleted successfully."))

        return super().delete(request, *args, **kwargs)


class ExportFastDataView(LoginRequiredMixin, View):
    """View for exporting user's fasting data in various formats."""

    def get(self, request, format="csv"):
        """Export fasting data in requested format."""
        # Get user's fasts
        fasts = Fast.objects.filter(user=request.user).order_by("-start_time")

        if format == "csv":
            return self._export_csv(fasts, request.user)
        if format == "json":
            return self._export_json(fasts, request.user)
        messages.error(request, _("Unsupported export format."))
        return redirect("fasting:fast_list")

    def _export_csv(self, fasts, user):
        """Export fasts as CSV."""
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="fasting_data_{datetime.now().strftime("%Y%m%d")}.csv"'
        )

        writer = csv.writer(response)

        # Write header
        writer.writerow(
            [
                "Start Time",
                "End Time",
                "Duration (hours)",
                "Status",
                "Emotional Status",
                "Comments",
            ],
        )

        # Write data
        for fast in fasts:
            writer.writerow(
                [
                    fast.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    fast.end_time.strftime("%Y-%m-%d %H:%M:%S")
                    if fast.end_time
                    else "",
                    fast.duration_hours if not fast.is_active else fast.elapsed_hours,
                    "Active" if fast.is_active else "Completed",
                    fast.get_emotional_status_display()
                    if fast.emotional_status
                    else "",
                    fast.comments or "",
                ],
            )

        return response

    def _export_json(self, fasts, user):
        """Export fasts as JSON."""
        response = HttpResponse(content_type="application/json")
        response["Content-Disposition"] = (
            f'attachment; filename="fasting_data_{datetime.now().strftime("%Y%m%d")}.json"'
        )

        data = {
            "exported_at": datetime.now().isoformat(),
            "user_email": user.email,
            "total_fasts": fasts.count(),
            "fasts": [],
        }

        for fast in fasts:
            fast_data = {
                "id": fast.id,
                "start_time": fast.start_time.isoformat(),
                "end_time": fast.end_time.isoformat() if fast.end_time else None,
                "duration_seconds": fast.duration_seconds
                if not fast.is_active
                else fast.elapsed_seconds,
                "is_active": fast.is_active,
                "emotional_status": fast.emotional_status,
                "emotional_status_display": fast.get_emotional_status_display()
                if fast.emotional_status
                else None,
                "comments": fast.comments or "",
            }
            data["fasts"].append(fast_data)

        response.write(json.dumps(data, indent=2))
        return response


def timer_update_view(request):
    """HTMX endpoint for updating elapsed time display."""
    if not request.user.is_authenticated:
        return render(request, "fasting/timer_fragment.html", {"active_fast": None})

    active_fast = SessionManager.get_user_active_fast(request)

    return render(request, "fasting/timer_fragment.html", {"active_fast": active_fast})
