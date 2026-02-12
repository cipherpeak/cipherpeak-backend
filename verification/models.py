from django.db import models
from django.utils import timezone


class ClientVerification(models.Model):

    client = models.ForeignKey(
        'clientapp.Client', 
        on_delete=models.CASCADE, 
        related_name='verifications'
    ) 
    
    # Verification
    verified_by = models.ForeignKey(
        'emplyees.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_content'
    )
    is_completed = models.BooleanField(default=False)
    verified_date = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True, null=True)
    

    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    
    def __str__(self):
        date_str = self.created_at.strftime('%Y-%m-%d') if self.created_at else "No Date"
        return f"{self.client.client_name} - {date_str}"
    


class MonthlyVerification(models.Model):
    clientverification = models.ForeignKey(
        ClientVerification,
        on_delete=models.CASCADE,
        related_name='monthly_verifications'
    )
    month = models.IntegerField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    posters_completed = models.IntegerField(default=0)
    videos_completed = models.IntegerField(default=0)
    posters_posted = models.IntegerField(default=0)
    videos_posted = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.clientverification.client.client_name} - {self.month}/{self.year} - {'Verified' if self.is_verified else 'Pending'}"
