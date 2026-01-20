from django.contrib import admin
from .models import ClientVerification

@admin.register(ClientVerification)
class ClientVerificationAdmin(admin.ModelAdmin):
    list_display = ('client', 'content_type', 'completion_date', 'verified_by', 'created_at', 'updated_at')
    list_filter = ('client', 'content_type', 'completion_date', 'verified_by')
    search_fields = ('client__client_name', 'description')
    
    fieldsets = (
        ('Client Information', {
            'fields': ('client', 'content_type')
        }),
        ('Verification Details', {
            'fields': ('completion_date', 'verified_by', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

