from django.db import models
from django.utils import timezone


class ClientVerification(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('video', 'Video'),
        ('poster', 'Poster'),  
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('youtube', 'YouTube'),
        ('linkedin', 'LinkedIn'),
        ('twitter', 'Twitter'),
        ('tiktok', 'TikTok'),
        ('other', 'Other'),
    ]
    
    client = models.ForeignKey(
        'clientapp.Client', 
        on_delete=models.CASCADE, 
        related_name='verifications'
    )
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES)
    
    # Content details
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    # Posting information
    posted_date = models.DateField(blank=True, null=True)
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES, blank=True, null=True)
    content_url = models.URLField(blank=True, null=True, verbose_name="Content URL")
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='posted')
    
    # Verification
    verified_by = models.ForeignKey(
        'emplyees.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_content'
    )
    verified_date = models.DateTimeField(null=True, blank=True)
    # verification_notes = models.TextField(blank=True, null=True)
    
    # Metadata
    created_by = models.ForeignKey(
        'emplyees.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_verifications'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-posted_date', '-created_at']
        indexes = [
            models.Index(fields=['client', 'posted_date']),
            models.Index(fields=['posted_date', 'status']),
        ]
        verbose_name = 'Posted Content'
        verbose_name_plural = 'Posted Contents'
    
    def __str__(self):
        return f"{self.client.client_name} - {self.get_content_type_display()} - {self.posted_date}"
    
    def save(self, *args, **kwargs):
        # Set default title if not provided
        if not self.title:
            self.title = f"{self.get_content_type_display()} - {self.posted_date.strftime('%Y-%m-%d')}"
        
        # Auto-set verification date if status changes to approved
        if self.status == 'approved' and not self.verified_date:
            self.verified_date = timezone.now()
        
        super().save(*args, **kwargs)
    
    def approve(self, user, notes=None):
        """Approve this posted content"""
        self.status = 'approved'
        self.verified_by = user
        self.verified_date = timezone.now()
        if notes:
            self.verification_notes = notes
        self.save()