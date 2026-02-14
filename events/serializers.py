from rest_framework import serializers
from .models import Event
from django.contrib.auth import get_user_model

User = get_user_model()


# event create serializer
class EventCreateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Event
        fields = [
            'id',
            'name',
            'description',
            'event_date',
            'event_type',
            'assigned_employee',
            'is_for_all_employees',
            'location',
            'status',
            'duration_minutes',
            'is_recurring',
            'recurrence_pattern'
        ]
        
    def validate(self, data):
        is_for_all = data.get('is_for_all_employees', False)
        assigned_emp = data.get('assigned_employee')
        
        if not is_for_all and not assigned_emp:
            raise serializers.ValidationError({"assigned_employee": "This field is required unless the event is for all employees."})
            
        return data
        
    



#user serializer
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']


# event list serializer
class EventListSerializer(serializers.ModelSerializer):
   
    assigned_employee_details = UserSerializer(source='assigned_employee', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_past_event = serializers.BooleanField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)

    class Meta:
        model = Event
        fields = [
            'id',
            'name',
            'description',
            'event_date',
            'event_type',
            'event_type_display',
            'assigned_employee',
            'assigned_employee_details',
            'location',
            'status',
            'status_display',
            'duration_minutes',
            'is_recurring',
            'recurrence_pattern',
            'is_for_all_employees',
            'is_past_event',
            'is_upcoming',
        ]


# event detail serializer
class EventDetailSerializer(serializers.ModelSerializer):
    
    assigned_employee_details = UserSerializer(source='assigned_employee', read_only=True)
    created_by_details = UserSerializer(source='created_by', read_only=True)
    is_past_event = serializers.BooleanField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    time_until_event = serializers.DurationField(read_only=True)
    event_duration_display = serializers.CharField(source='get_event_duration_display', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id',
            'name',
            'description',
            'event_date',
            'event_type',
            'event_type_display',
            'assigned_employee',
            'assigned_employee_details',
            'location',
            'created_by',
            'created_by_details',
            'created_at',
            'updated_at',
            'status',
            'status_display',
            'duration_minutes',
            'is_recurring',
            'recurrence_pattern',
            'is_past_event',
            'is_upcoming',
            'time_until_event',
            'is_for_all_employees',
            'event_duration_display'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']


# event update serializer
class EventUpdateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Event
        fields = [
            'id',
            'name',
            'description',
            'event_date',
            'event_type',
            'assigned_employee',
            'is_for_all_employees',
            'location',
            'status',
            'duration_minutes',
            'is_recurring',
            'recurrence_pattern'
        ]
    
    def validate_event_date(self, value):
        # We allow updates to past events (e.g. updating description or status)
        # However, if the date is being CHANGED, we might want to check something.
        # For now, removing the past date restriction to fix the update issue.
        return value



