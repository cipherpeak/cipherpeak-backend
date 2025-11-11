from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone





class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('scheduled', 'Scheduled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    TASK_TYPES = [
        ('seo', 'SEO'),
        ('social_media', 'Social Media'),
        ('content', 'Content Creation'),
        ('ppc', 'PPC Campaign'),
        ('website', 'Website Development'),
        ('email', 'Email Marketing'),
        ('analytics', 'Analytics'),
        ('client_meeting', 'Client Meeting'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assignee = models.ForeignKey('emplyees.CustomUser', on_delete=models.CASCADE, related_name='tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    client = models.ForeignKey('clientapp.Client', on_delete=models.CASCADE, related_name='tasks',blank=True,null=True) 
    due_date = models.DateTimeField()
    scheduled_date = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    created_by = models.ForeignKey('emplyees.CustomUser', on_delete=models.CASCADE, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Auto-update completed_at when status changes to completed
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != 'completed':
            self.completed_at = None
        super().save(*args, **kwargs)