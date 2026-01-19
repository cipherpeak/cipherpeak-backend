# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import *

admin.site.register(Client)
admin.site.register(ClientDocument)
admin.site.register(ClientPayment)

