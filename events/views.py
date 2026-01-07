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
    EventStatusUpdateSerializer
)


 

# event create view
class EventCreateView(APIView):
    """
    View for creating events
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Create event with permission check"""
        # Check if user has permission to create events
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
    """
    View for listing events with manual filtering, searching and ordering.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Base queryset - exclude deleted events
        queryset = Event.objects.filter(is_deleted=False)
        
        # Role-based visibility: Employees only see their assigned events
        user = request.user
        if not user.is_superuser and user.role not in ['superuser', 'admin', 'director', 'managing_director']:
            queryset = queryset.filter(assigned_employee=user)

        # 1. Searching
        search_query = request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                models.Q(name__icontains=search_query) |
                models.Q(description__icontains=search_query) |
                models.Q(location__icontains=search_query) |
                models.Q(assigned_employee__first_name__icontains=search_query) |
                models.Q(assigned_employee__last_name__icontains=search_query)
            )

        # 2. Filtering
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

        # Date range filtering
        start_date = request.query_params.get('start_date', None)
        if start_date:
            queryset = queryset.filter(event_date__date__gte=start_date)
            
        end_date = request.query_params.get('end_date', None)
        if end_date:
            queryset = queryset.filter(event_date__date__lte=end_date)

        # 3. Ordering
        ordering = request.query_params.get('ordering', 'event_date')
        valid_ordering_fields = ['event_date', '-event_date', 'created_at', '-created_at', 'status', '-status']
        if ordering not in valid_ordering_fields:
            ordering = 'event_date'
        
        queryset = queryset.order_by(ordering).select_related('assigned_employee', 'created_by')

        # Serialization
        serializer = EventListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

#event detail view
class EventDetailView(APIView):
    """
    View for retrieving a specific event
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, id):
        """Helper to get the event and enforce accessibility rules"""
        try:
            event = Event.objects.get(id=id, is_deleted=False)
            
            # Filter based on user role - Employees see only their assigned events
            user = self.request.user
            if not user.is_superuser and user.role not in ['superuser', 'admin', 'director', 'managing_director']:
                if event.assigned_employee != user:
                    return None
            
            return event
        except Event.DoesNotExist:
            return None

    def get(self, request, id):
        """Retrieve event details"""
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
    """
    View for updating a specific event
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, id):
        """Helper to get the event and enforce accessibility rules"""
        try:
            event = Event.objects.get(id=id, is_deleted=False)
            
            # Filter based on user role
            user = self.request.user
            if not user.is_superuser and user.role not in ['director', 'managing_director']:
                if event.assigned_employee != user:
                    return None
            
            return event
        except Event.DoesNotExist:
            return None

    def put(self, request, id):
        """Full update of an event"""
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
        """Partial update of an event"""
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
    """
    View for soft deleting a specific event
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, id):
        """Helper to get the event and enforce accessibility rules"""
        try:
            event = Event.objects.get(id=id, is_deleted=False)
            
            # Filter based on user role to prevent unauthorized deletion
            user = self.request.user
            if not user.is_superuser and user.role not in ['superuser', 'admin']:
                if event.assigned_employee != user:
                    return None
            
            return event
        except Event.DoesNotExist:
            return None
    
    def delete(self, request, id):
        """Perform soft delete"""
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
        
    










class EventStatusUpdateView(generics.UpdateAPIView):
    """
    View for updating only the event status
    """
    queryset = Event.objects.all()
    serializer_class = EventStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def perform_update(self, serializer):
        instance = serializer.save()
        # Add any additional logic when status changes
        # For example, send notifications, update related records, etc.
        if instance.status == 'completed':
            # Logic for completed events
            pass
        elif instance.status == 'cancelled':
            # Logic for cancelled events
            pass

class EventStatsView(generics.GenericAPIView):
    """
    View for getting event statistics
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        total_events = Event.objects.count()
        scheduled_events = Event.objects.filter(status='scheduled').count()
        in_progress_events = Event.objects.filter(status='in_progress').count()
        completed_events = Event.objects.filter(status='completed').count()
        cancelled_events = Event.objects.filter(status='cancelled').count()
        postponed_events = Event.objects.filter(status='postponed').count()
        
        # Past events
        past_events = Event.objects.filter(event_date__lt=timezone.now()).count()
        
        # Upcoming events (next 7 days)
        upcoming_events = Event.objects.filter(
            event_date__gte=timezone.now(),
            event_date__lte=timezone.now() + timezone.timedelta(days=7)
        ).count()
        
        # Events by type
        events_by_type = Event.objects.values('event_type').annotate(
            count=models.Count('id'),
            display_name=models.Case(
                *[models.When(event_type=choice[0], then=models.Value(choice[1])) for choice in Event.EVENT_TYPE_CHOICES],
                output_field=models.CharField()
            )
        )
        
        # Events by status
        events_by_status = Event.objects.values('status').annotate(
            count=models.Count('id'),
            display_name=models.Case(
                *[models.When(status=choice[0], then=models.Value(choice[1])) for choice in Event.STATUS_CHOICES],
                output_field=models.CharField()
            )
        )
        
        # Events by assigned employee
        events_by_employee = Event.objects.values(
            'assigned_employee__id', 
            'assigned_employee__first_name', 
            'assigned_employee__last_name'
        ).annotate(count=models.Count('id'))
        
        # Recurring events count
        recurring_events = Event.objects.filter(is_recurring=True).count()
        
        # Events by recurrence pattern
        events_by_recurrence = Event.objects.filter(is_recurring=True).values(
            'recurrence_pattern'
        ).annotate(count=models.Count('id'))
        
        stats = {
            'total_events': total_events,
            'scheduled_events': scheduled_events,
            'in_progress_events': in_progress_events,
            'completed_events': completed_events,
            'cancelled_events': cancelled_events,
            'postponed_events': postponed_events,
            'past_events': past_events,
            'upcoming_events': upcoming_events,
            'recurring_events': recurring_events,
            'events_by_type': list(events_by_type),
            'events_by_status': list(events_by_status),
            'events_by_employee': list(events_by_employee),
            'events_by_recurrence': list(events_by_recurrence),
        }
        
        return Response(stats, status=status.HTTP_200_OK)

class MyEventsView(generics.ListAPIView):
    """
    View for listing events assigned to the current user
    """
    serializer_class = EventListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description', 'location']
    ordering_fields = ['created_at', 'event_date', 'event_type']
    ordering = ['event_date']

    def get_queryset(self):
        """
        Return events assigned to the current user
        """
        queryset = Event.objects.filter(assigned_employee=self.request.user)
        
        # Filter by event type if provided
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter past events
        past_events = self.request.query_params.get('past_events')
        if past_events and past_events.lower() == 'true':
            queryset = queryset.filter(event_date__lt=timezone.now())
        
        # Filter upcoming events
        upcoming = self.request.query_params.get('upcoming')
        if upcoming and upcoming.lower() == 'true':
            queryset = queryset.filter(
                event_date__gte=timezone.now(),
                event_date__lte=timezone.now() + timezone.timedelta(days=7)
            )
        
        return queryset.select_related('assigned_employee', 'created_by')

class EventsCreatedByMeView(generics.ListAPIView):
    """
    View for listing events created by the current user
    """
    serializer_class = EventListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description', 'assigned_employee__first_name', 'assigned_employee__last_name', 'location']
    ordering_fields = ['created_at', 'event_date', 'event_type']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Return events created by the current user
        """
        queryset = Event.objects.filter(created_by=self.request.user)
        
        # Filter by event type if provided
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by assigned employee if provided
        assigned_employee_id = self.request.query_params.get('assigned_employee')
        if assigned_employee_id:
            queryset = queryset.filter(assigned_employee_id=assigned_employee_id)
        
        return queryset.select_related('assigned_employee', 'created_by')

class EmployeeEventsView(generics.ListAPIView):
    """
    View for listing events for a specific employee
    """
    serializer_class = EventListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description', 'location']
    ordering_fields = ['created_at', 'event_date', 'event_type', 'status']
    ordering = ['event_date']

    def get_queryset(self):
        """
        Return events for a specific employee
        """
        employee_id = self.kwargs.get('employee_id')
        queryset = Event.objects.filter(assigned_employee_id=employee_id)
        
        # Filter by event type if provided
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter past events
        past_events = self.request.query_params.get('past_events')
        if past_events and past_events.lower() == 'true':
            queryset = queryset.filter(event_date__lt=timezone.now())
        
        # Filter upcoming events
        upcoming = self.request.query_params.get('upcoming')
        if upcoming and upcoming.lower() == 'true':
            queryset = queryset.filter(
                event_date__gte=timezone.now(),
                event_date__lte=timezone.now() + timezone.timedelta(days=7)
            )
        
        return queryset.select_related('assigned_employee', 'created_by')

class CalendarEventsView(generics.ListAPIView):
    """
    View for listing events for calendar display with date range filtering
    """
    serializer_class = EventListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return events filtered by date range for calendar display
        """
        queryset = Event.objects.all()
        
        # Required date range parameters
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if not start_date or not end_date:
            # Default to current month if no date range provided
            today = timezone.now().date()
            start_date = today.replace(day=1)
            end_date = (today.replace(day=1) + timezone.timedelta(days=32)).replace(day=1) - timezone.timedelta(days=1)
        
        queryset = queryset.filter(
            event_date__date__gte=start_date,
            event_date__date__lte=end_date
        )
        
        # Additional optional filters
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        assigned_employee_id = self.request.query_params.get('assigned_employee')
        if assigned_employee_id:
            queryset = queryset.filter(assigned_employee_id=assigned_employee_id)
        
        return queryset.select_related('assigned_employee', 'created_by')


    