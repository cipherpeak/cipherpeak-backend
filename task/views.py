# tasks/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import models
from django.utils import timezone
from .models import Task
from .serializers import TaskSerializer, TaskCreateSerializer, TaskUpdateSerializer, TaskStatusUpdateSerializer

class TaskListCreateView(generics.ListCreateAPIView):
    """
    View for listing and creating tasks
    """
    queryset = Task.objects.filter(is_deleted=False)
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'description', 'assignee__first_name', 'assignee__last_name', 'client__client_name']
    ordering_fields = ['created_at', 'due_date', 'priority', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TaskCreateSerializer
        return TaskSerializer

    def get_queryset(self):
        """
        Optionally filter by status, priority, task_type, assignee, client, or overdue
        """
        queryset = Task.objects.filter(is_deleted=False)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by priority if provided
        priority_filter = self.request.query_params.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        # Filter by task type if provided
        task_type = self.request.query_params.get('task_type')
        if task_type:
            queryset = queryset.filter(task_type=task_type)
        
        # Filter by assignee if provided
        assignee_id = self.request.query_params.get('assignee')
        if assignee_id:
            queryset = queryset.filter(assignee_id=assignee_id)
        
        # Filter by client if provided
        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        # Filter overdue tasks
        overdue = self.request.query_params.get('overdue')
        if overdue and overdue.lower() == 'true':
            queryset = queryset.filter(due_date__lt=timezone.now(), status__in=['pending', 'in_progress'])
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(due_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(due_date__lte=end_date)
        
        return queryset.select_related('assignee', 'created_by', 'client')

    def perform_create(self, serializer):
        """Set the created_by field to the current user"""
        serializer.save(created_by=self.request.user)

class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View for retrieving, updating and deleting a specific task
    """
    queryset = Task.objects.filter(is_deleted=False) 
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TaskUpdateSerializer
        return TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(is_deleted=False).select_related('assignee', 'created_by', 'client')

class TaskStatusUpdateView(generics.UpdateAPIView):
    """
    View for updating only the task status
    """
    queryset = Task.objects.filter(is_deleted=False)
    serializer_class = TaskStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def perform_update(self, serializer):
        instance = serializer.save()
        # Auto-update completed_at when status changes to completed
        if instance.status == 'completed' and not instance.completed_at:
            instance.completed_at = timezone.now()
            instance.save()
        elif instance.status != 'completed':
            instance.completed_at = None
            instance.save()

class TaskStatsView(generics.GenericAPIView):
    """
    View for getting task statistics
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        base_queryset = Task.objects.filter(is_deleted=False)
        total_tasks = base_queryset.count()
        pending_tasks = base_queryset.filter(status='pending').count()
        in_progress_tasks = base_queryset.filter(status='in_progress').count()
        completed_tasks = base_queryset.filter(status='completed').count()
        scheduled_tasks = base_queryset.filter(status='scheduled').count()
        
        # Overdue tasks
        overdue_tasks = base_queryset.filter(
            due_date__lt=timezone.now(), 
            status__in=['pending', 'in_progress']
        ).count()
        
        # Tasks by priority
        tasks_by_priority = base_queryset.values('priority').annotate(count=models.Count('id'))

        # Tasks by status
        tasks_by_status = base_queryset.values('status').annotate(count=models.Count('id'))
        
        # Tasks by type
        tasks_by_type = base_queryset.values('task_type').annotate(count=models.Count('id'))
        
        # Tasks by assignee
        tasks_by_assignee = base_queryset.values(
            'assignee__id', 
            'assignee__first_name', 
            'assignee__last_name'
        ).annotate(count=models.Count('id'))
        
        # Tasks by client (new)
        tasks_by_client = base_queryset.values(
            'client__id', 
            'client__client_name'
        ).annotate(count=models.Count('id'))
        
        stats = {
            'total_tasks': total_tasks,
            'pending_tasks': pending_tasks,
            'in_progress_tasks': in_progress_tasks,
            'completed_tasks': completed_tasks,
            'scheduled_tasks': scheduled_tasks,
            'overdue_tasks': overdue_tasks,
            'tasks_by_priority': list(tasks_by_priority),
            'tasks_by_status': list(tasks_by_status),
            'tasks_by_type': list(tasks_by_type),
            'tasks_by_assignee': list(tasks_by_assignee),
            'tasks_by_client': list(tasks_by_client),  # Added client stats
        }
        
        return Response(stats, status=status.HTTP_200_OK)

class MyTasksView(generics.ListAPIView):
    """
    View for listing tasks assigned to the current user
    """
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'description', 'client__client_name']
    ordering_fields = ['created_at', 'due_date', 'priority']
    ordering = ['-due_date']

    def get_queryset(self):
        """
        Return tasks assigned to the current user
        """
        queryset = Task.objects.filter(assignee=self.request.user, is_deleted=False)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by priority if provided
        priority_filter = self.request.query_params.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        # Filter by client if provided
        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        # Filter overdue tasks
        overdue = self.request.query_params.get('overdue')
        if overdue and overdue.lower() == 'true':
            queryset = queryset.filter(due_date__lt=timezone.now(), status__in=['pending', 'in_progress'])
        
        return queryset.select_related('assignee', 'created_by', 'client')

class TasksCreatedByMeView(generics.ListAPIView):
    """
    View for listing tasks created by the current user
    """
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'description', 'assignee__first_name', 'assignee__last_name', 'client__client_name']
    ordering_fields = ['created_at', 'due_date', 'priority']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Return tasks created by the current user
        """
        queryset = Task.objects.filter(created_by=self.request.user, is_deleted=False)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by priority if provided
        priority_filter = self.request.query_params.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        # Filter by client if provided
        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        return queryset.select_related('assignee', 'created_by', 'client')

class ClientTasksView(generics.ListAPIView):
    """
    View for listing tasks for a specific client
    """
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'description', 'assignee__first_name', 'assignee__last_name']
    ordering_fields = ['created_at', 'due_date', 'priority', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Return tasks for a specific client
        """
        client_id = self.kwargs.get('client_id')
        queryset = Task.objects.filter(client_id=client_id, is_deleted=False)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by priority if provided
        priority_filter = self.request.query_params.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        # Filter by task type if provided
        task_type = self.request.query_params.get('task_type')
        if task_type:
            queryset = queryset.filter(task_type=task_type)
        
        # Filter overdue tasks
        overdue = self.request.query_params.get('overdue')
        if overdue and overdue.lower() == 'true':
            queryset = queryset.filter(due_date__lt=timezone.now(), status__in=['pending', 'in_progress'])
        
        return queryset.select_related('assignee', 'created_by', 'client')


class TaskSoftDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, task_id):
        """Helper to get the task and check if it exists or is deleted"""
        try:
            task = Task.objects.get(id=task_id)
            if task.is_deleted:
                raise Task.DoesNotExist
            return task
        except Task.DoesNotExist:
            raise

    def delete(self, request, id):
        """Soft delete the task"""
        try:
            instance = self.get_object(id)
            
            instance.is_deleted = True
            instance.deleted_at = timezone.now()
            instance.save()
            
            return Response(
                {
                    'message': f'Task "{instance.title}" deleted successfully.',
                    'task_id': instance.id,
                    'task_title': instance.title,
                    'deleted_at': instance.deleted_at
                },
                status=status.HTTP_200_OK
            )
        except Task.DoesNotExist:
            return Response(
                {'error': 'Task not found or already deleted.'},
                status=status.HTTP_404_NOT_FOUND
            )