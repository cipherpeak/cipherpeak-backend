from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import models
from django.utils import timezone
from .models import Event
from .serializers import EventSerializer, EventCreateSerializer, EventUpdateSerializer, EventStatusUpdateSerializer

class EventListCreateView(generics.ListCreateAPIView):
    """
    View for listing and creating events
    """
    queryset = Event.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description', 'assigned_employee__first_name', 'assigned_employee__last_name', 'location']
    ordering_fields = ['created_at', 'event_date', 'event_type', 'status']
    ordering = ['event_date']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EventCreateSerializer
        return EventSerializer

    def get_queryset(self):
        """
        Optionally filter by event_type, status, assigned_employee, or date range
        """
        queryset = Event.objects.all()
        
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
        
        # Filter by created by if provided
        created_by_id = self.request.query_params.get('created_by')
        if created_by_id:
            queryset = queryset.filter(created_by_id=created_by_id)
        
        # Filter recurring events
        is_recurring = self.request.query_params.get('is_recurring')
        if is_recurring:
            if is_recurring.lower() == 'true':
                queryset = queryset.filter(is_recurring=True)
            elif is_recurring.lower() == 'false':
                queryset = queryset.filter(is_recurring=False)
        
        # Filter past events
        past_events = self.request.query_params.get('past_events')
        if past_events and past_events.lower() == 'true':
            queryset = queryset.filter(event_date__lt=timezone.now())
        
        # Filter upcoming events (next 7 days)
        upcoming = self.request.query_params.get('upcoming')
        if upcoming and upcoming.lower() == 'true':
            queryset = queryset.filter(
                event_date__gte=timezone.now(),
                event_date__lte=timezone.now() + timezone.timedelta(days=7)
            )
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(event_date__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(event_date__date__lte=end_date)
        
        return queryset.select_related('assigned_employee', 'created_by')

    def perform_create(self, serializer):
        """Set the created_by field to the current user"""
        serializer.save(created_by=self.request.user)

class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View for retrieving, updating and deleting a specific event
    """
    queryset = Event.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return EventUpdateSerializer
        return EventSerializer

    def get_queryset(self):
        return Event.objects.select_related('assigned_employee', 'created_by')

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
    serializer_class = EventSerializer
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
    serializer_class = EventSerializer
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
    serializer_class = EventSerializer
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
    serializer_class = EventSerializer
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