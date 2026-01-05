# tasks/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import models
from django.utils import timezone
from .models import Task
from .serializers import (
    TaskCreateSerializer, 
    TaskUpdateSerializer, 
    TaskListSerializer, 
    TaskSerializer, 
    TaskDetailSerializer,
    TaskStatusUpdateSerializer
)



# create task view
class TaskCreateView(APIView):
    """
    View for creating tasks
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Create task with permission check"""
        # Check if user has permission to create tasks
        if request.user.role not in ['director', 'managing_director'] and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied. Only Superusers and Admins can create tasks."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = TaskCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(
                {
                    "message": "Task created successfully!",
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



#task list view
class TaskListView(APIView):
    """
    View for listing tasks with manual filtering, searching and ordering.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Base queryset - exclude deleted tasks
        queryset = Task.objects.filter(is_deleted=False)
        
        # Role-based visibility: Employees only see their own tasks
        user = request.user
        if not user.is_superuser and user.role not in ['superuser', 'admin']:
            queryset = queryset.filter(assignee=user)

        # 1. Searching
        search_query = request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                models.Q(title__icontains=search_query) |
                models.Q(description__icontains=search_query) |
                models.Q(assignee__first_name__icontains=search_query) |
                models.Q(assignee__last_name__icontains=search_query) |
                models.Q(client__client_name__icontains=search_query)
            )

        # 2. Filtering
        status_filter = request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        priority_filter = request.query_params.get('priority', None)
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)

        task_type = request.query_params.get('task_type', None)
        if task_type:
            queryset = queryset.filter(task_type=task_type)

        assignee_id = request.query_params.get('assignee', None)
        if assignee_id:
            queryset = queryset.filter(assignee_id=assignee_id)

        client_id = request.query_params.get('client', None)
        if client_id:
            queryset = queryset.filter(client_id=client_id)

        # Overdue tasks
        overdue = request.query_params.get('overdue', None)
        if overdue and overdue.lower() == 'true':
            queryset = queryset.filter(
                due_date__lt=timezone.now(), 
                status__in=['pending', 'in_progress']
            )

        # Date range filtering
        start_date = request.query_params.get('start_date', None)
        if start_date:
            queryset = queryset.filter(due_date__gte=start_date)
            
        end_date = request.query_params.get('end_date', None)
        if end_date:
            queryset = queryset.filter(due_date__lte=end_date)

        # 3. Ordering
        ordering = request.query_params.get('ordering', '-created_at')
        valid_ordering_fields = ['created_at', '-created_at', 'due_date', '-due_date', 'priority', '-priority', 'status', '-status']
        if ordering not in valid_ordering_fields:
            ordering = '-created_at'
        
        queryset = queryset.order_by(ordering).select_related('assignee', 'created_by', 'client')

        # Serialization
        serializer = TaskListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


#task detail view
class TaskDetailView(APIView):
    """
    View for retrieving and updating a specific task
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, id):
        """Helper to get the task and enforce accessibility rules"""
        try:
            task = Task.objects.get(id=id, is_deleted=False)
            
            # Filter based on user role - Employees see only their assigned tasks
            user = self.request.user
            if not user.is_superuser and user.role not in ['director', 'managing_director']:
                if task.assignee != user:
                    return None
            
            return task
        except Task.DoesNotExist:
            return None

    def get(self, request, id):
        """Retrieve task details"""
        task = self.get_object(id)
        if not task:
            return Response(
                {"error": "Task not found or access denied."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = TaskDetailSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)


#task update view
class TaskUpdateView(APIView):
    """
    View for updating a specific task
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, id):
        """Helper to get the task and enforce accessibility rules"""
        try:
            task = Task.objects.get(id=id, is_deleted=False)
            
            # Filter based on user role - Employees see only their assigned tasks
            user = self.request.user
            if not user.is_superuser and user.role not in ['director', 'managing_director']:
                if task.assignee != user:
                    return None
            
            return task
        except Task.DoesNotExist:
            return None

    def put(self, request, id):
        """Full update of a task"""
        task = self.get_object(id)
        if not task:
            return Response(
                {"error": "Task not found or access denied."},
               
            )
            
        serializer = TaskUpdateSerializer(task, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Task updated successfully"},
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        """Partial update of a task"""
        task = self.get_object(id)
        if not task:
            return Response(
                {"error": "Task not found or access denied."},
                
            )
            
        serializer = TaskUpdateSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Task updated successfully"},
                
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, task_id):
        """Helper to get the task and check if it exists or is deleted"""
        try:
            task = Task.objects.get(id=task_id)
            
            # Check permissions
            user = self.request.user
            if not user.is_superuser and user.role not in ['superuser', 'admin']:
                if task.assignee != user:
                    raise Task.DoesNotExist
            
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
                    'message': f'Task deleted successfully.',
                },
                status=status.HTTP_200_OK
            )
        except Task.DoesNotExist:
            return Response(
                {'error': 'Task not found or already deleted.'},
                status=status.HTTP_404_NOT_FOUND
            )















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


