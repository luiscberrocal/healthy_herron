from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import Fast


@admin.register(Fast)
class FastAdmin(admin.ModelAdmin):
    """Admin interface for Fast model."""
    
    list_display = [
        'user',
        'start_time',
        'end_time',
        'duration_display',
        'emotional_status',
        'is_active',
        'created_display'
    ]
    
    list_filter = [
        'emotional_status',
        'created',
        ('end_time', admin.EmptyFieldListFilter),  # Filter by active/completed
        'start_time',
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'comments',
    ]
    
    readonly_fields = [
        'created',
        'modified',
        'duration_display',
        'elapsed_time_display',
        'user_link'
    ]
    
    fieldsets = (
        ('Fast Information', {
            'fields': (
                'user_link',
                'start_time',
                'end_time',
                'duration_display',
                'elapsed_time_display'
            )
        }),
        ('Status & Feedback', {
            'fields': (
                'emotional_status',
                'comments'
            )
        }),
        ('Metadata', {
            'fields': (
                'created',
                'modified'
            ),
            'classes': ('collapse',)
        })
    )
    
    # Default ordering
    ordering = ['-start_time']
    
    # Items per page
    list_per_page = 25
    
    # Enable date hierarchy navigation
    date_hierarchy = 'start_time'
    
    def duration_display(self, obj):
        """Display duration in a human-readable format."""
        if obj.duration:
            total_seconds = int(obj.duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            
            if hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        return "-"
    duration_display.short_description = "Duration"
    duration_display.admin_order_field = 'end_time'
    
    def elapsed_time_display(self, obj):
        """Display elapsed time for active fasts."""
        if obj.is_active:
            elapsed = obj.elapsed_time
            if elapsed:
                total_seconds = int(elapsed.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                
                if hours > 0:
                    return format_html(
                        '<span style="color: #28a745; font-weight: bold;">{}</span>',
                        f"{hours}h {minutes}m (active)"
                    )
                else:
                    return format_html(
                        '<span style="color: #28a745; font-weight: bold;">{}</span>',
                        f"{minutes}m (active)"
                    )
        return "-"
    elapsed_time_display.short_description = "Elapsed Time"
    
    def created_display(self, obj):
        """Display creation date in a readable format."""
        return obj.created.strftime('%Y-%m-%d %H:%M')
    created_display.short_description = "Created"
    created_display.admin_order_field = 'created'
    
    def user_link(self, obj):
        """Create a link to the user's admin page."""
        url = reverse('admin:users_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user)
    user_link.short_description = "User"
    user_link.admin_order_field = 'user__username'
    
    def is_active(self, obj):
        """Display active status with visual indicator."""
        if obj.is_active:
            return format_html(
                '<span style="color: #28a745;">●</span> Active'
            )
        else:
            return format_html(
                '<span style="color: #6c757d;">●</span> Completed'
            )
    is_active.short_description = "Status"
    is_active.boolean = True
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion only for superusers."""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Allow changes for staff users."""
        return request.user.is_staff
    
    def has_add_permission(self, request):
        """Allow adding new fasts for staff users."""
        return request.user.is_staff
    
    def save_model(self, request, obj, form, change):
        """Custom save method to handle validation."""
        try:
            obj.full_clean()
            super().save_model(request, obj, form, change)
        except Exception as e:
            self.message_user(request, f"Error saving fast: {e}", level='ERROR')
    
    actions = ['mark_completed', 'export_selected_fasts']
    
    def mark_completed(self, request, queryset):
        """Admin action to mark active fasts as completed."""
        active_fasts = queryset.filter(end_time__isnull=True)
        updated_count = 0
        
        for fast in active_fasts:
            fast.end_time = timezone.now()
            fast.emotional_status = 'satisfied'  # Default status
            try:
                fast.full_clean()
                fast.save()
                updated_count += 1
            except Exception:
                continue
        
        if updated_count:
            self.message_user(
                request,
                f"Successfully marked {updated_count} fast(s) as completed."
            )
        else:
            self.message_user(
                request,
                "No active fasts were found to mark as completed.",
                level='WARNING'
            )
    mark_completed.short_description = "Mark selected active fasts as completed"
    
    def export_selected_fasts(self, request, queryset):
        """Admin action to export selected fasts."""
        # This would typically redirect to an export view
        # For now, just show a message
        count = queryset.count()
        self.message_user(
            request,
            f"Export functionality for {count} fast(s) would be implemented here."
        )
    export_selected_fasts.short_description = "Export selected fasts"


# Optional: Inline admin for viewing fasts within user admin
class FastInline(admin.TabularInline):
    """Inline admin for displaying fasts in user admin."""
    model = Fast
    extra = 0
    readonly_fields = ['created', 'duration_display']
    fields = ['start_time', 'end_time', 'emotional_status', 'duration_display', 'created']
    
    def duration_display(self, obj):
        """Display duration in inline."""
        if obj.duration:
            total_seconds = int(obj.duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        return "-"
    duration_display.short_description = "Duration"