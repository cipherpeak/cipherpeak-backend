from django.contrib import admin
from .models import ClientVerification

@admin.register(ClientVerification)
class ClientVerificationAdmin(admin.ModelAdmin):
    list_display = ('client', 'content_type', 'completion_date', 'verified_by')
    list_filter = ('content_type', 'verified_by', 'completion_date')
    search_fields = ('client__client_name', 'description')
