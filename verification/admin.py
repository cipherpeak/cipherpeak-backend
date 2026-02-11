from django.contrib import admin
from .models import ClientVerification
from clientapp.models import Client  # Import Client from clientapp

@admin.register(ClientVerification)
class ClientVerificationAdmin(admin.ModelAdmin):
    list_display = ('client', 'content_type', 'posted_date', 'status', 'platform', 'created_at')
    list_filter = ('content_type', 'status', 'platform', 'posted_date')
    search_fields = ('client__client_name', 'title', 'description')
    readonly_fields = ('created_at', 'updated_at', 'verified_date')
    date_hierarchy = 'posted_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client', 'verified_by')