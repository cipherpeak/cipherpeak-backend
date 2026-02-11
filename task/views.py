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
    TaskDetailSerializer,
    
)

# create task view
class TaskCreateView(APIView):
   
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
       
        if request.user.role not in ['director', 'managing_director'] and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied. Only Superusers and Admins can create tasks."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = TaskCreateSerializer(data=request.data)
        if serializer.is_valid():
            task = serializer.save(created_by=request.user)
            # Use DetailSerializer to return full data
            response_serializer = TaskDetailSerializer(task)
            return Response(
                {
                    "message": "Task created successfully!",
                    "task": response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#task list view
class TaskListView(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        
        queryset = Task.objects.filter(is_deleted=False)
        
        user = request.user
        if not user.is_superuser and user.role not in ['superuser', 'admin']:
            queryset = queryset.filter(assignee=user)

        search_query = request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                models.Q(title__icontains=search_query) |
                models.Q(description__icontains=search_query) |
                models.Q(assignee__first_name__icontains=search_query) |
                models.Q(assignee__last_name__icontains=search_query) |
                models.Q(client__client_name__icontains=search_query)
            )

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

        ordering = request.query_params.get('ordering', '-created_at')
        valid_ordering_fields = ['created_at', '-created_at', 'priority', '-priority', 'status', '-status']
        if ordering not in valid_ordering_fields:
            ordering = '-created_at'
        
        queryset = queryset.order_by(ordering).select_related('assignee', 'created_by', 'client')
        serializer = TaskListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


#task detail view
class TaskDetailView(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, id):
        
        try:
            task = Task.objects.get(id=id, is_deleted=False)
            user = self.request.user
            if not user.is_superuser and user.role not in ['director', 'managing_director']:
                if task.assignee != user:
                    return None
            
            return task
        except Task.DoesNotExist:
            return None

    def get(self, request, id):
        
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
    
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, id):
        
        try:
            task = Task.objects.get(id=id, is_deleted=False)
            user = self.request.user
            if not user.is_superuser and user.role not in ['director', 'managing_director']:
                if task.assignee != user:
                    return None
            
            return task
        except Task.DoesNotExist:
            return None

    def put(self, request, id):
        task = self.get_object(id)
        if not task:
            return Response(
                {"error": "Task not found or access denied."},
               
            )
            
        serializer = TaskUpdateSerializer(task, data=request.data)
        if serializer.is_valid():
            task = serializer.save()
            response_serializer = TaskDetailSerializer(task)
            return Response(
                {
                    "message": "Task updated successfully",
                    "task": response_serializer.data
                }
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
       
        task = self.get_object(id)
        if not task:
            return Response(
                {"error": "Task not found or access denied."},
                
            )
            
        serializer = TaskUpdateSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            task = serializer.save()
            response_serializer = TaskDetailSerializer(task)
            return Response(
                {
                    "message": "Task updated successfully",
                    "task": response_serializer.data
                }
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#task delete view
class TaskDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, task_id):
         
        try:
            task = Task.objects.get(id=task_id)
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















#task status update view
class TaskStatusUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            task = Task.objects.get(id=id)
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Permission check
        user = request.user
        if not user.is_superuser and user.role not in ['admin', 'director', 'managing_director']:
            if task.assignee != user:
                return Response(
                    {"error": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN
                )

        new_status = request.data.get('status')
        if not new_status:
            return Response(
                {"error": "Status is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update status
        task.status = new_status
        task.save()
        
        return Response(
            {
                "message": "Task status updated successfully",
                "status": task.status,
                "status_display": task.get_status_display()
            },
            status=status.HTTP_200_OK
        )
