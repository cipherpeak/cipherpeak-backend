# client/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import date, timedelta
import calendar

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
import calendar
from datetime import date

class Client(models.Model):
    # Client Type Choices
    CLIENT_TYPE_CHOICES = [
        ('company', 'Company'),
        ('brand', 'Brand'),
        ('individual', 'Individual'),
        ('agency', 'Agency'),
    ]
    
    # Industry Choices
    INDUSTRY_CHOICES = [
        ('fashion', 'Fashion & Apparel'),
        ('beauty', 'Beauty & Cosmetics'),
        ('health', 'Health & Wellness'),
        ('food_beverage', 'Food & Beverage'),
        ('technology', 'Technology'),
        ('education', 'Education'),
        ('entertainment', 'Entertainment'),
        ('real_estate', 'Real Estate'),
        ('hospitality', 'Hospitality'),
        ('retail', 'Retail'),
        ('other', 'Other'),
    ]
    
    # Status Choices
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_hold', 'On Hold'),
        ('terminated', 'Terminated'),
        ('prospect', 'Prospect'),
    ]

    # Payment Cycle Choices
    PAYMENT_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom'),
    ]

    # Payment Status Choices
    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('overdue', 'Overdue'),
        ('partial', 'Partial Payment'),
        ('early_paid', 'Early Paid'),  # New status for early payments
    ]

    # Payment Timing Choices
    PAYMENT_TIMING_CHOICES = [
        ('on_time', 'On Time'),
        ('early', 'Early'),
        ('late', 'Late'),
    ]
    
    # Basic Client Information
    client_name = models.CharField(max_length=255, unique=True)
    client_type = models.CharField(max_length=20, choices=CLIENT_TYPE_CHOICES, default='company')
    industry = models.CharField(max_length=50, choices=INDUSTRY_CHOICES, blank=True, null=True)
    
    # Client Owner/Contact Information
    owner_name = models.CharField(max_length=255, blank=True, null=True)
    contact_person_name = models.CharField(max_length=255, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Social Media Handles
    instagram_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="Instagram ID/Handle")
    facebook_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="Facebook ID/Page")
    youtube_channel = models.CharField(max_length=255, blank=True, null=True, verbose_name="YouTube Channel")
    google_my_business = models.CharField(max_length=255, blank=True, null=True, verbose_name="Google My Business")
    linkedin_url = models.URLField(blank=True, null=True, verbose_name="LinkedIn URL")
    twitter_handle = models.CharField(max_length=255, blank=True, null=True, verbose_name="Twitter Handle")
    
    # Monthly Content Requirements
    videos_per_month = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Number of Videos per Month"
    )
    posters_per_month = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Number of Posters per Month"
    )
    reels_per_month = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Number of Reels per Month"
    )
    stories_per_month = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Number of Stories per Month"
    )
    
    # Client Status & Timeline
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='prospect')
    onboarding_date = models.DateField(default=timezone.now)
    contract_start_date = models.DateField(blank=True, null=True)
    contract_end_date = models.DateField(blank=True, null=True)
    
    # Payment Information
    payment_cycle = models.CharField(
        max_length=20, 
        choices=PAYMENT_CYCLE_CHOICES, 
        default='monthly',
        verbose_name="Payment Cycle"
    )
    payment_date = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MinValueValidator(31)],
        verbose_name="Payment Date (Day of Month)",
        help_text="Enter the day of month (1-31) when payment is due"
    )
    next_payment_date = models.DateField(
        blank=True, 
        null=True,
        verbose_name="Next Payment Due Date",
        help_text="Automatically calculated next payment due date"
    )
    current_month_payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name="Current Month Payment Status"
    )
    last_payment_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Last Payment Date"
    )
    monthly_retainer = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0)],
        verbose_name="Monthly Retainer Fee"
    )
    
    # New fields for payment timing and early payments
    payment_timing = models.CharField(
        max_length=10,
        choices=PAYMENT_TIMING_CHOICES,
        default='on_time',
        verbose_name="Payment Timing",
        help_text="Indicates if payment was made early, on time, or late"
    )
    early_payment_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Early Payment Date",
        help_text="Date when early payment was made"
    )
    early_payment_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        verbose_name="Early Payment Amount"
    )
    early_payment_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Early Payment Notes",
        help_text="Any notes regarding early payment"
    )
    
    # Additional Details
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    
    # Business Information
    website = models.URLField(blank=True, null=True)
    business_registration_number = models.CharField(max_length=100, blank=True, null=True)
    tax_id = models.CharField(max_length=100, blank=True, null=True)
    
    description = models.TextField(blank=True, null=True, verbose_name="Client Description")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['client_name']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
    
    def __str__(self):
        return f"{self.client_name} ({self.get_client_type_display()})"
    
    def save(self, *args, **kwargs):
        """Override save to calculate next_payment_date"""
        # Calculate next payment date if payment_date is set
        if self.payment_date:
            self.calculate_next_payment_date()
        
        # Update payment status based on dates
        self.update_payment_status()
        
        super().save(*args, **kwargs)
    
    def calculate_next_payment_date(self):
        """Calculate the next payment due date based on payment date"""
        today = timezone.now().date()
        
        # Get the current year and month
        current_year = today.year
        current_month = today.month
        
        # Get the last day of current month
        _, last_day_current_month = calendar.monthrange(current_year, current_month)
        
        # Adjust payment date if it exceeds the last day of the month
        adjusted_payment_date = min(self.payment_date, last_day_current_month)
        
        # Create payment date for current month
        current_month_payment_date = date(current_year, current_month, adjusted_payment_date)
        
        if today <= current_month_payment_date:
            # If today is on or before the payment date this month
            self.next_payment_date = current_month_payment_date
        else:
            # If payment date for this month has passed, calculate for next month
            if current_month == 12:
                next_year = current_year + 1
                next_month = 1
            else:
                next_year = current_year
                next_month = current_month + 1
            
            # Get the last day of next month
            _, last_day_next_month = calendar.monthrange(next_year, next_month)
            adjusted_payment_date_next = min(self.payment_date, last_day_next_month)
            
            self.next_payment_date = date(next_year, next_month, adjusted_payment_date_next)
    
    def update_payment_status(self):
        """Update payment status based on current date and next payment date"""
        today = timezone.now().date()
        
        if self.current_month_payment_status == 'paid':
            # If payment is marked as paid, don't change status automatically
            return
        
        if self.next_payment_date:
            if today > self.next_payment_date:
                self.current_month_payment_status = 'overdue'
            else:
                self.current_month_payment_status = 'pending'
    
    def mark_payment_as_paid(self, payment_date=None, amount=None, notes=None, is_early=False):
        """Mark payment as paid with optional early payment tracking"""
        today = payment_date or timezone.now().date()
        
        # Update payment status and timing
        self.current_month_payment_status = 'paid'
        self.last_payment_date = today
        
        # Determine payment timing
        if is_early:
            self.current_month_payment_status = 'early_paid'
            self.payment_timing = 'early'
            self.early_payment_date = today
            self.early_payment_amount = amount or self.monthly_retainer
            self.early_payment_notes = notes
        else:
            # Check if payment is early, on time, or late
            if self.next_payment_date:
                if today < self.next_payment_date:
                    self.payment_timing = 'early'
                    self.early_payment_date = today
                    self.early_payment_amount = amount or self.monthly_retainer
                    self.early_payment_notes = notes or "Early payment made"
                elif today == self.next_payment_date:
                    self.payment_timing = 'on_time'
                else:
                    self.payment_timing = 'late'
            else:
                self.payment_timing = 'on_time'
        
        # Calculate next payment date after payment
        self.calculate_next_payment_date_after_payment()
        
        self.save()
    
    def mark_early_payment(self, payment_date, amount=None, notes=None):
        """Specifically mark an early payment"""
        self.mark_payment_as_paid(
            payment_date=payment_date,
            amount=amount,
            notes=notes,
            is_early=True
        )
    
    def calculate_next_payment_date_after_payment(self):
        """Calculate next payment date after a payment is made"""
        today = self.last_payment_date or timezone.now().date()
        
        if self.payment_cycle == 'monthly':
            # For monthly payments, calculate next month
            if today.month == 12:
                next_year = today.year + 1
                next_month = 1
            else:
                next_year = today.year
                next_month = today.month + 1
            
            # Get the last day of next month
            _, last_day_next_month = calendar.monthrange(next_year, next_month)
            adjusted_payment_date = min(self.payment_date, last_day_next_month)
            
            self.next_payment_date = date(next_year, next_month, adjusted_payment_date)
            
        elif self.payment_cycle == 'quarterly':
            # For quarterly payments, add 3 months
            next_month = today.month + 3
            next_year = today.year
            if next_month > 12:
                next_month -= 12
                next_year += 1
            
            _, last_day_next_quarter = calendar.monthrange(next_year, next_month)
            adjusted_payment_date = min(self.payment_date, last_day_next_quarter)
            
            self.next_payment_date = date(next_year, next_month, adjusted_payment_date)
            
        elif self.payment_cycle == 'yearly':
            # For yearly payments, add 1 year
            next_year = today.year + 1
            _, last_day_next_year = calendar.monthrange(next_year, today.month)
            adjusted_payment_date = min(self.payment_date, last_day_next_year)
            
            self.next_payment_date = date(next_year, today.month, adjusted_payment_date)
    
    def reset_payment_status_for_new_month(self):
        """Reset payment status for new month (to be called at beginning of each month)"""
        today = timezone.now().date()
        
        # Only reset if we're in a new month and payment was marked as paid for previous month
        if (self.last_payment_date and 
            self.last_payment_date.month != today.month and 
            self.current_month_payment_status in ['paid', 'early_paid']):
            
            self.current_month_payment_status = 'pending'
            self.payment_timing = 'on_time'  # Reset timing for new month
            self.early_payment_date = None
            self.early_payment_amount = None
            self.early_payment_notes = None
            self.save()
    
    @property
    def total_content_per_month(self):
        """Calculate total content pieces per month"""
        return (self.videos_per_month + self.posters_per_month + 
                self.reels_per_month + self.stories_per_month)
    
    @property
    def is_active_client(self):
        """Check if client is currently active"""
        return self.status == 'active'
    
    @property
    def contract_duration(self):
        """Calculate contract duration in months"""
        if self.contract_start_date and self.contract_end_date:
            delta = self.contract_end_date - self.contract_start_date
            return delta.days // 30  # Approximate months
        return None

    @property
    def is_payment_overdue(self):
        """Check if payment is overdue"""
        return self.current_month_payment_status == 'overdue'

    @property
    def days_until_next_payment(self):
        """Calculate days until next payment is due"""
        if self.next_payment_date:
            delta = self.next_payment_date - timezone.now().date()
            return delta.days
        return None

    @property
    def payment_status_display(self):
        """Get payment status as string"""
        if self.current_month_payment_status == 'paid':
            return "Paid"
        elif self.current_month_payment_status == 'early_paid':
            return "Early Paid"
        elif self.current_month_payment_status == 'overdue':
            return "Overdue"
        elif self.days_until_next_payment == 0:
            return "Due Today"
        elif self.days_until_next_payment and self.days_until_next_payment <= 7:
            return f"Due in {self.days_until_next_payment} days"
        else:
            return "Pending"

    @property
    def is_early_payment(self):
        """Check if the last payment was made early"""
        return self.current_month_payment_status == 'early_paid' or self.payment_timing == 'early'

    @property
    def early_payment_days(self):
        """Calculate how many days early the payment was made"""
        if self.early_payment_date and self.next_payment_date:
            # Calculate what would have been the payment date for that period
            payment_year = self.early_payment_date.year
            payment_month = self.early_payment_date.month
            
            # Get the last day of the payment month
            _, last_day_month = calendar.monthrange(payment_year, payment_month)
            adjusted_payment_date = min(self.payment_date, last_day_month)
            
            original_due_date = date(payment_year, payment_month, adjusted_payment_date)
            
            if self.early_payment_date < original_due_date:
                return (original_due_date - self.early_payment_date).days
        return 0
class ClientDocument(models.Model):
    """Model to store client-related documents"""
    DOCUMENT_TYPES = [
        ('contract', 'Contract Agreement'),
        ('proposal', 'Proposal'),
        ('invoice', 'Invoice'),
        ('gst_document','GST Document'),
        ('nda', 'Non-Disclosure Agreement'),
        ('brand_guidelines', 'Brand Guidelines'),
        ('marketing_plan', 'Marketing Plan'),
        ('performance_report', 'Performance Report'),
        ('other', 'Other'),
    ]
    
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200,blank=True, null=True)
    file = models.FileField(upload_to='client_documents/%Y/%m/%d/')
    description = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        'emplyees.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_client_documents'
    )
    
    def __str__(self):
        return f"{self.client.client_name} - {self.get_document_type_display()} - {self.title}"

