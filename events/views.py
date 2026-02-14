from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import models
from django.utils import timezone
from .models import Event
from rest_framework.views import APIView
from .serializers import (
    EventDetailSerializer,
    EventListSerializer,
    EventCreateSerializer, 
    EventUpdateSerializer, 
    
)
 

# event create view
class EventCreateView(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        
        if request.user.role not in ['director', 'managing_director'] and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied. Only Superusers and Admins can create events."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = EventCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(
                {
                    "message": "Event created successfully!",
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#event list view
class EventListView(APIView):
   
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        
        queryset = Event.objects.filter(is_deleted=False)
        
        user = request.user
        if not user.is_superuser and user.role not in ['superuser', 'admin', 'director', 'managing_director']:
            queryset = queryset.filter(
                models.Q(assigned_employee=user) | 
                models.Q(is_for_all_employees=True)
            )

        search_query = request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                models.Q(name__icontains=search_query) |
                models.Q(description__icontains=search_query) |
                models.Q(location__icontains=search_query) |
                models.Q(assigned_employee__first_name__icontains=search_query) |
                models.Q(assigned_employee__last_name__icontains=search_query)
            )

        event_type = request.query_params.get('event_type', None)
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        status_filter = request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        assigned_employee_id = request.query_params.get('assigned_employee', None)
        if assigned_employee_id:
            queryset = queryset.filter(assigned_employee_id=assigned_employee_id)

        created_by_id = request.query_params.get('created_by', None)
        if created_by_id:
            queryset = queryset.filter(created_by_id=created_by_id)

        is_recurring = request.query_params.get('is_recurring', None)
        if is_recurring:
            if is_recurring.lower() == 'true':
                queryset = queryset.filter(is_recurring=True)
            elif is_recurring.lower() == 'false':
                queryset = queryset.filter(is_recurring=False)

        past_events = request.query_params.get('past_events', None)
        if past_events and past_events.lower() == 'true':
            queryset = queryset.filter(event_date__lt=timezone.now())

        upcoming = request.query_params.get('upcoming', None)
        if upcoming and upcoming.lower() == 'true':
            queryset = queryset.filter(
                event_date__gte=timezone.now(),
                event_date__lte=timezone.now() + timezone.timedelta(days=7)
            )

        start_date = request.query_params.get('start_date', None)
        if start_date:
            queryset = queryset.filter(event_date__date__gte=start_date)
            
        end_date = request.query_params.get('end_date', None)
        if end_date:
            queryset = queryset.filter(event_date__date__lte=end_date)

        ordering = request.query_params.get('ordering', 'event_date')
        valid_ordering_fields = ['event_date', '-event_date', 'created_at', '-created_at', 'status', '-status']
        if ordering not in valid_ordering_fields:
            ordering = 'event_date'
        
        queryset = queryset.order_by(ordering).select_related('assigned_employee', 'created_by')

        serializer = EventListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

#event detail view
class EventDetailView(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, id):
        
        try:
            event = Event.objects.get(id=id, is_deleted=False)
            user = self.request.user
            if not user.is_superuser and user.role not in ['superuser', 'admin', 'director', 'managing_director']:
                if event.assigned_employee != user and not event.is_for_all_employees:
                    return None
            
            return event
        except Event.DoesNotExist:
            return None

    def get(self, request, id):
        
        event = self.get_object(id)
        if not event:
            return Response(
                {"error": "Event not found or access denied."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = EventDetailSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)

#event update view
class EventUpdateView(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, id):
       
        try:
            event = Event.objects.get(id=id, is_deleted=False)
            
            user = self.request.user
            if not user.is_superuser and user.role not in ['director', 'managing_director']:
                if event.assigned_employee != user:
                    return None
            
            return event
        except Event.DoesNotExist:
            return None

    def put(self, request, id):
      
        event = self.get_object(id)
        if not event:
            return Response(
                {"error": "Event not found or access denied."},
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = EventUpdateSerializer(event, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Event updated successfully"},
                
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        
        event = self.get_object(id)
        if not event:
            return Response(
                {"error": "Event not found or access denied."},
                
            )
            
        serializer = EventUpdateSerializer(event, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Event updated successfully"},
               
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# event delete view
class EventDeleteView(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, id):
       
        try:
            event = Event.objects.get(id=id, is_deleted=False)
            user = self.request.user
            if not user.is_superuser and user.role not in ['superuser', 'admin']:
                if event.assigned_employee != user:
                    return None
            
            return event
        except Event.DoesNotExist:
            return None
    
    def delete(self, request, id):
        
        event = self.get_object(id)
        if not event:
            return Response(
                {"error": "Event not found or access denied."},
                
            )
            
        event.soft_delete(user=request.user)
        return Response(
            {
                "message": "Event deleted successfully!"
            },
            status=status.HTTP_200_OK
        )
    
    
