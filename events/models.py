
# Create your models here.
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator
from django.utils import timezone

User = get_user_model()

class Event(models.Model):
    """
    Event model for managing various types of events like meetings, special days, etc.
    """
    
    # Event type choices
    EVENT_TYPE_CHOICES = [
        ('meeting', 'Meeting'),
        ('special_day', 'Special Day'),
        ('conference', 'Conference'),
        ('workshop', 'Workshop'),
        ('training', 'Training'),
        ('team_building', 'Team Building'),
        ('client_meeting', 'Client Meeting'),
        ('project_review', 'Project Review'),
        ('birthday', 'Birthday'),
        ('anniversary', 'Anniversary'),
        ('holiday', 'Holiday'),
        ('deadline', 'Deadline'),
        ('presentation', 'Presentation'),
        ('other', 'Other'),
    ]
    
    # Event name and description
    name = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(2)],
        help_text="Name of the event"
    )
    
    description = models.TextField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="Detailed description of the event"
    )
    
    # Event date and time
    event_date = models.DateTimeField(
        help_text="Date and time when the event will occur"
    )
    
    # Event type
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPE_CHOICES,
        default='meeting',
        help_text="Type of the event"
    )
    
    # Assigned employee (Foreign Key to User model)
    assigned_employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_events',
        help_text="Employee assigned to this event"
    )
    
    # Location information
    location = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        help_text="Physical or virtual location of the event"
    )
    
    # Additional useful fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_events',
        help_text="User who created this event"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Status field for event lifecycle
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('postponed', 'Postponed'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        help_text="Current status of the event"
    )
    
    # Duration field (optional but useful)
    duration_minutes = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Duration of the event in minutes"
    )
    
    # Recurring event support (optional)
    is_recurring = models.BooleanField(
        default=False,
        help_text="Whether this event repeats regularly"
    )
    
    recurrence_pattern = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
        ],
        help_text="How often the event repeats"
    )
    
    class Meta:
        db_table = 'events'
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
        ordering = ['event_date']
        indexes = [
            models.Index(fields=['event_date']),
            models.Index(fields=['event_type']),
            models.Index(fields=['assigned_employee']),
            models.Index(fields=['status']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(event_date__gte=timezone.now()),
                name='event_date_future'
            )
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_event_type_display()} - {self.event_date.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def is_past_event(self):
        """Check if the event has already occurred"""
        return self.event_date < timezone.now()
    
    @property
    def is_upcoming(self):
        """Check if the event is within the next 24 hours"""
        time_until_event = self.event_date - timezone.now()
        return time_until_event.total_seconds() <= 86400 and time_until_event.total_seconds() > 0
    
    @property
    def time_until_event(self):
        """Calculate time remaining until event"""
        return self.event_date - timezone.now()
    
    def get_event_duration_display(self):
        """Display duration in human-readable format"""
        if self.duration_minutes:
            if self.duration_minutes < 60:
                return f"{self.duration_minutes} minutes"
            else:
                hours = self.duration_minutes // 60
                minutes = self.duration_minutes % 60
                if minutes == 0:
                    return f"{hours} hour{'s' if hours > 1 else ''}"
                else:
                    return f"{hours} hour{'s' if hours > 1 else ''} {minutes} minutes"
        return "Not specified"