# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser, EmployeeDocument, EmployeeMedia, LeaveManagement, SalaryHistory, CameraDepartment

admin.site.register(CustomUser)
admin.site.register(CameraDepartment)
admin.site.register(LeaveManagement)
admin.site.register(SalaryHistory)

