from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'event_type', 
        'event_date', 
        'assigned_employee', 
        'location', 
        'status',
        'is_past_event'
    ]
    list_filter = ['event_type', 'status', 'is_recurring', 'event_date', 'assigned_employee']
    search_fields = ['name', 'description', 'location', 'assigned_employee__username']
    date_hierarchy = 'event_date'
    ordering = ['-event_date']
    readonly_fields = ['created_at', 'updated_at', 'is_past_event', 'is_upcoming']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'event_type', 'status')
        }),
        ('Date & Time', {
            'fields': ('event_date', 'duration_minutes')
        }),
        ('People & Location', {
            'fields': ('assigned_employee', 'location', 'created_by')
        }),
        ('Recurrence', {
            'fields': ('is_recurring', 'recurrence_pattern'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'is_past_event', 'is_upcoming'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('assigned_employee', 'created_by')