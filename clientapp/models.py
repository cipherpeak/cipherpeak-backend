from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import date, timedelta
import calendar



class Client(models.Model):
    
    CLIENT_TYPE_CHOICES = [
        ('company', 'Company'),
        ('brand', 'Brand'),
        ('individual', 'Individual'),
        ('agency', 'Agency'),
    ]
    
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
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_hold', 'On Hold'),
        ('terminated', 'Terminated'),
        ('prospect', 'Prospect'),
    ]

    PAYMENT_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom'),
    ]


    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('overdue', 'Overdue'),
        ('partial', 'Partial Payment'),
        ('early_paid', 'Early Paid'), 
    ]


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
        validators=[MinValueValidator(1), MaxValueValidator(31)],
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

    payment_timing = models.CharField(
        max_length=10,
        choices=PAYMENT_TIMING_CHOICES,
        default='on_time',
        verbose_name="Payment Timing",
        help_text="Indicates if payment was made early, on time, or late"
    )
    
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    
    website = models.URLField(blank=True, null=True)
    business_registration_number = models.CharField(max_length=100, blank=True, null=True)
    tax_id = models.CharField(max_length=100, blank=True, null=True)
    
    description = models.TextField(blank=True, null=True, verbose_name="Client Description")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['client_name']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
    
    def __str__(self):
        return f"{self.client_name} ({self.get_client_type_display()})"
    
    def save(self, *args, **kwargs):
       
        if self.payment_date:
            self.calculate_next_payment_date()
        
        self.update_payment_status()
        
        super().save(*args, **kwargs)
    
    def calculate_next_payment_date(self):
    
        today = timezone.now().date()
        
        current_year = today.year
        current_month = today.month
        
        _, last_day_current_month = calendar.monthrange(current_year, current_month)
        adjusted_payment_date = min(self.payment_date, last_day_current_month)
        
        current_month_payment_date = date(current_year, current_month, adjusted_payment_date)
        
        if today <= current_month_payment_date:
        
            self.next_payment_date = current_month_payment_date
        else:
    
            if current_month == 12:
                next_year = current_year + 1
                next_month = 1
            else:
                next_year = current_year
                next_month = current_month + 1
            
            _, last_day_next_month = calendar.monthrange(next_year, next_month)
            adjusted_payment_date_next = min(self.payment_date, last_day_next_month)
            
            self.next_payment_date = date(next_year, next_month, adjusted_payment_date_next)
    
    def update_payment_status(self):
        
        today = timezone.now().date()
        
        if self.current_month_payment_status in ['paid', 'early_paid']:
            return
        
        if self.next_payment_date:
            if today >= self.next_payment_date:
                self.current_month_payment_status = 'overdue'
            else:
                self.current_month_payment_status = 'pending'
    
    def mark_payment_as_paid(self, payment_date=None, amount=None, notes=None):
        
        today = payment_date or timezone.now().date()
        self.current_month_payment_status = 'paid'
        self.last_payment_date = today
        if self.next_payment_date:
            if today < self.next_payment_date:
                self.payment_timing = 'early'
                self.current_month_payment_status = 'early_paid'
            elif today == self.next_payment_date:
                self.payment_timing = 'on_time'
            else:
                self.payment_timing = 'late'
        else:
            self.payment_timing = 'on_time'
        
        self.calculate_next_payment_date_after_payment()
        
        self.save()
    
    def calculate_next_payment_date_after_payment(self):
        today = self.last_payment_date or timezone.now().date()
        
        if self.payment_cycle == 'monthly':
            
            if today.month == 12:
                next_year = today.year + 1
                next_month = 1
            else:
                next_year = today.year
                next_month = today.month + 1
            _, last_day_next_month = calendar.monthrange(next_year, next_month)
            adjusted_payment_date = min(self.payment_date, last_day_next_month)
            
            self.next_payment_date = date(next_year, next_month, adjusted_payment_date)
            
        elif self.payment_cycle == 'quarterly':
            next_month = today.month + 3
            next_year = today.year
            if next_month > 12:
                next_month -= 12
                next_year += 1
            
            _, last_day_next_quarter = calendar.monthrange(next_year, next_month)
            adjusted_payment_date = min(self.payment_date, last_day_next_quarter)
            
            self.next_payment_date = date(next_year, next_month, adjusted_payment_date)
            
        elif self.payment_cycle == 'yearly':
            next_year = today.year + 1
            _, last_day_next_year = calendar.monthrange(next_year, today.month)
            adjusted_payment_date = min(self.payment_date, last_day_next_year)
            
            self.next_payment_date = date(next_year, today.month, adjusted_payment_date)
    
    @property
    def total_content_per_month(self):
        return (self.videos_per_month + self.posters_per_month + 
                self.reels_per_month + self.stories_per_month)
    
    @property
    def is_active_client(self):
        return self.status == 'active'
    
    @property
    def contract_duration(self):
        if self.contract_start_date and self.contract_end_date:
            delta = self.contract_end_date - self.contract_start_date
            return delta.days // 30
        return None

    @property
    def is_payment_overdue(self):
        return self.current_month_payment_status == 'overdue'

    @property
    def days_until_next_payment(self):
        if self.next_payment_date:
            delta = self.next_payment_date - timezone.now().date()
            return delta.days
        return None

    @property
    def payment_status_display(self):
        if self.current_month_payment_status == 'paid':
            return "Paid"
        elif self.current_month_payment_status == 'overdue':
            return "Overdue"
        elif self.days_until_next_payment == 0:
            return "Due Today"
        elif self.days_until_next_payment and self.days_until_next_payment <= 7:
            return f"Due in {self.days_until_next_payment} days"
        else:
            return "Pending"
    # In clientapp/models.py, add these methods to Client class:

    @property
    def current_month_verification(self):
        """Get current month's verification"""
        from verification.models import ContentVerification
        today = timezone.now()
        
        verification = ContentVerification.objects.filter(
            client=self,
            month=today.month,
            year=today.year
        ).first()
        
        return verification

    @property
    def verification_status(self):
        """Get current verification status"""
        verification = self.current_month_verification
        if verification:
            return verification.verification_status
        return 'pending'

    @property
    def verification_progress(self):
        """Get verification progress percentage"""
        verification = self.current_month_verification
        if verification:
            return verification.progress_percentage
        return 0

    def get_monthly_verification(self, month, year):
        """Get verification for specific month/year"""
        from verification.models import ContentVerification
        return ContentVerification.objects.filter(
            client=self,
            month=month,
            year=year
        ).first()


class ClientDocument(models.Model):
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
    file = models.FileField(upload_to='client_documents/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        'emplyees.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_client_documents'
    )
    
    def __str__(self):
        return f"{self.client.client_name} - {self.get_document_type_display()}"


class ClientAdminNote(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='admin_notes'
    )
    note = models.TextField(verbose_name="Admin Remarks/Note")
    created_by = models.ForeignKey(
        'emplyees.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='client_admin_notes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Client Admin Note"
        verbose_name_plural = "Client Admin Notes"
    
    def __str__(self):
        return f"Note for {self.client.client_name} - {self.created_at.strftime('%Y-%m-%d')}"


class ClientPayment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('early_paid', 'Early Paid'),
        ('overdue', 'Overdue'),
        ('partial', 'Partial Payment'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('upi', 'UPI'),
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('online', 'Online Payment'),
    ]
    
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='client_payments'
    )
    
    # Period Information
    month = models.IntegerField()
    year = models.IntegerField()
    
    # Financial Details
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Scheduling
    scheduled_date = models.DateField()
    
    # Payment Details
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    payment_date = models.DateTimeField(blank=True, null=True)
    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
        null=True
    )
    processed_by = models.ForeignKey(
        'emplyees.CustomUser',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='processed_client_payments'
    )
    
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Client Payment Record'
        verbose_name_plural = 'Client Payment Records'
        unique_together = ('client', 'month', 'year')
        ordering = ['-year', '-month']
    
    def __str__(self):
        return f"{self.client.client_name} - {self.month}/{self.year} ({self.status})"
    
    def save(self, *args, **kwargs):
        if self.net_amount is None or not self.pk:
            self.net_amount = self.amount + self.tax_amount - self.discount
        super().save(*args, **kwargs)

