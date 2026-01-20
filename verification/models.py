from django.db import models
from django.utils import timezone

class ClientVerification(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('video', 'Video'),
        ('poster', 'Poster'),
        ('reel', 'Reel'),
        ('story', 'Story'),
    ]

    client = models.ForeignKey('clientapp.Client', on_delete=models.CASCADE, related_name='verifications')
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES)
    completion_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    
    verified_by = models.ForeignKey(
        'emplyees.CustomUser', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='verified_content'
    )
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-completion_date']
        verbose_name = 'Content Verification'
        verbose_name_plural = 'Content Verifications'

    def __str__(self):
        return f"{self.client.client_name} - {self.get_content_type_display()} - {self.completion_date}"
