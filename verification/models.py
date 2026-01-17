from django.db import models
from clientapp.models import Client, ClientPayment
from django.db.models import Q
from django.utils import timezone

class ContentVerification(models.Model):
    VERIFICATION_STATUS = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('pending_payment', 'Pending Payment'),
        ('completed', 'Completed'),
    )
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='verifications')
    month = models.PositiveIntegerField()
    year = models.PositiveIntegerField()
    
    # Content counts - actual submissions
    video = models.PositiveIntegerField(default=0)
    poster = models.PositiveIntegerField(default=0)
    reels = models.PositiveIntegerField(default=0)
    story = models.PositiveIntegerField(default=0)
    
    # Verification status (manually set or auto-calculated)
    verification_status = models.CharField(
        max_length=20, 
        choices=VERIFICATION_STATUS, 
        default='pending'
    )
    
    payment = models.ForeignKey(ClientPayment, on_delete=models.SET_NULL, null=True, blank=True, related_name='verifications')
    verified_by = models.ForeignKey('emplyees.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('client', 'month', 'year')
        ordering = ['-year', '-month', 'client__client_name']

    def __str__(self):
        return f"{self.client.client_name} - {self.month}/{self.year} Verification"

    @property
    def videos_target(self):
        """Get video target from client"""
        return self.client.videos_per_month
    
    @property
    def posters_target(self):
        """Get poster target from client"""
        return self.client.posters_per_month
    
    @property
    def reels_target(self):
        """Get reels target from client"""
        return self.client.reels_per_month
    
    @property
    def stories_target(self):
        """Get stories target from client"""
        return self.client.stories_per_month
    
    @property
    def payment_status(self):
        """Get payment status for this verification's month/year"""
        # First check if linked payment exists
        if self.payment:
            return self.payment.status
        
        # If no linked payment, check ClientPayment table
        try:
            payment = ClientPayment.objects.get(
                client=self.client,
                month=self.month,
                year=self.year
            )
            return payment.status
        except ClientPayment.DoesNotExist:
            return 'no_payment'
    
    @property
    def is_paid(self):
        """Check if payment is made for this month - returns True/False"""
        return self.payment_status in ['paid', 'early_paid']
        

    def calculate_status(self):
        """Calculate status based on content targets AND payment."""
        # Check if content targets are met
        content_completed = (
            self.videos_target > 0 and self.video >= self.videos_target and
            self.posters_target > 0 and self.poster >= self.posters_target and
            self.reels_target > 0 and self.reels >= self.reels_target and
            self.stories_target > 0 and self.story >= self.stories_target
        )
        
        # Check payment status
        is_paid = self.is_paid
        
        if content_completed and is_paid:
            return 'completed'
        elif content_completed and not is_paid:
            return 'pending_payment'
        elif self.video > 0 or self.poster > 0 or self.reels > 0 or self.story > 0:
            return 'in_progress'
        else:
            return 'pending'

    def save(self, *args, **kwargs):
        # Auto-calculate status before saving
        self.verification_status = self.calculate_status()
        
        # Auto-link payment if exists for this month/year
        if not self.payment:
            try:
                payment = ClientPayment.objects.get(
                    client=self.client,
                    month=self.month,
                    year=self.year
                )
                self.payment = payment
            except ClientPayment.DoesNotExist:
                pass  # No payment found
        
        # Auto-set verification timestamp if status is completed
        if self.verification_status == 'completed' and not self.verified_at:
            self.verified_at = timezone.now()
        
        # Clear verified_at if status changes from completed
        if self.verification_status != 'completed' and self.verified_at:
            self.verified_at = None
            
        super().save(*args, **kwargs)

    @property
    def progress_percentage(self):
        """Calculate overall progress percentage"""
        total_targets = sum([
            self.videos_target,
            self.posters_target,
            self.reels_target,
            self.stories_target
        ])
        
        if total_targets == 0:
            return 0
            
        total_submitted = sum([
            self.video,
            self.poster,
            self.reels,
            self.story
        ])
        
        return min(100, int((total_submitted / total_targets) * 100))

    @classmethod
    def get_pending_verifications(cls, month=None, year=None):
        """Get all pending verifications for a specific month/year."""
        if month is None:
            month = timezone.now().month
        if year is None:
            year = timezone.now().year
            
        return cls.objects.filter(
            month=month,
            year=year,
            verification_status__in=['pending', 'in_progress', 'pending_payment']
        )
