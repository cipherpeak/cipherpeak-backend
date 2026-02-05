from django.db import models
from django.utils import timezone

class ClientVerification(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('video', 'Video'),
        ('poster', 'Poster'),  
    ]
    client = models.ForeignKey('clientapp.Client', on_delete=models.CASCADE, related_name='verifications')
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES)
    verified_by = models.ForeignKey(
        'emplyees.CustomUser', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='verified_content'
    )
    
    completion_date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    

    def __str__(self):
        return f"{self.client.client_name} - {self.completion_date}"
