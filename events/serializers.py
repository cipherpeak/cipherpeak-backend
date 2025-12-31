from rest_framework import serializers
from .models import Event
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']

class EventSerializer(serializers.ModelSerializer):
    """Serializer for Event model"""
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
            'event_duration_display'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

class EventCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating events"""
    
    class Meta:
        model = Event
        fields = [
            'name',
            'description',
            'event_date',
            'event_type',
            'assigned_employee',
            'location',
            'status',
            'duration_minutes',
            'is_recurring',
            'recurrence_pattern'
        ]
        
    
    def validate_event_date(self, value):
        """Validate that event date is in the future"""
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError("Event date cannot be in the past.")
        return value

class EventUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating events"""
    
    class Meta:
        model = Event
        fields = [
            'name',
            'description',
            'event_date',
            'event_type',
            'assigned_employee',
            'location',
            'status',
            'duration_minutes',
            'is_recurring',
            'recurrence_pattern'
        ]
    
    def validate_event_date(self, value):
        """Validate that event date is in the future"""
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError("Event date cannot be in the past.")
        return value

class EventStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating only event status"""
    
    class Meta:
        model = Event
        fields = ['status']