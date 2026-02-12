from django.contrib import admin
from .models import ClientVerification, MonthlyVerification

admin.site.register(ClientVerification)
admin.site.register(MonthlyVerification)