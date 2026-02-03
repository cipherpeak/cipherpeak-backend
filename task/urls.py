# tasks/urls.py
from django.urls import path
from . import views

urlpatterns = [
    #create task
    path('create/', views.TaskCreateView.as_view(), name='task-create'),

    #update task
    path('update-task/<int:id>/', views.TaskUpdateView.as_view(), name='task-update'),

    #list task
    path('tasks/', views.TaskListView.as_view(), name="task-list"),

    #detail task
    path('task_details/<int:id>/',views.TaskDetailView.as_view(),name="tak-detail"),

    #delete task
    path('task/<int:id>/delete/', views.TaskDeleteView.as_view(), name='delete_task'),  

    #status update
    path('task/<int:id>/status/', views.TaskStatusUpdateView.as_view(), name='task-status-update'),

    
]