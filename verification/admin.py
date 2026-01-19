from django.contrib import admin
from .models import ClientVerification

@admin.register(ClientVerification)
class ClientVerificationAdmin(admin.ModelAdmin):
    list_display = ('client', 'content_type', 'completion_date', 'verified_by', 'created_at')
    list_filter = ('client', 'content_type', 'completion_date')
    search_fields = ('client__client_name', 'description')
    date_hierarchy = 'completion_date'
