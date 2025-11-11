# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser, EmployeeDocument, EmployeeMedia, LeaveRecord, SalaryHistory

admin.site.register(CustomUser)