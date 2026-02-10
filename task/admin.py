from django.contrib import admin
from .models import Task

# Register your models here.

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'assignee', 'status', 'priority', 'task_type', 'created_at')
    list_filter = ('status', 'priority', 'task_type')
    search_fields = ('title', 'description')