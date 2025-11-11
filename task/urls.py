# tasks/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Task URLs
    path('create/', views.TaskListCreateView.as_view(), name='task-list-create'),
    path('create/<int:id>/', views.TaskDetailView.as_view(), name='task-detail'),
    path('create/<int:id>/status/', views.TaskStatusUpdateView.as_view(), name='task-status-update'),
    path('stats/', views.TaskStatsView.as_view(), name='task-stats'),
    path('my-tasks/', views.MyTasksView.as_view(), name='my-tasks'),
    path('created-by-me/', views.TasksCreatedByMeView.as_view(), name='tasks-created-by-me'),
]