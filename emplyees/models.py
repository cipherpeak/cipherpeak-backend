from django.db import models
from decimal import Decimal
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone

class CustomUser(AbstractUser):
    
    ROLE_CHOICES = [
        ('superuser', 'Superuser'),
        ('admin', 'Admin'),
        ('employee', 'Employee'),
    ]

    USER_TYPE_CHOICES = [
        ('developer', 'Developer'),
        ('camera_department', 'Camera Department'),
        ('editor', 'Editor'),
        ('marketer', 'Marketer'),
        ('hr', 'HR'),
        ('manager', 'Manager'),
        ('content_creator', 'Content Creator'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('on_leave', 'On Leave'),
        ('probation_period', 'Probation Period'),
        ('notice_period', 'Notice Period'),
        ('inactive', 'Inactive'),
        ('terminated', 'Terminated'),
    ]
    
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='employee'
    )

    user_type = models.CharField(
        max_length=50,
        choices=USER_TYPE_CHOICES,
        blank=True,
        null=True,
        help_text='Specific role type for the employee'
    )
    
    salary = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0)]
    )
    
    current_status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active'
    )

    profile_image = models.ImageField(
        upload_to='profile_images/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='Profile Image',
        help_text='Upload a profile picture (optional)'
    )
    
    joining_date = models.DateField(default=timezone.now)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=10, 
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other')
        ], 
        blank=True, 
        null=True
    )
    
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"


class EmployeeDocument(models.Model):


    DOCUMENT_TYPES = [
        ('resume', 'Resume/CV'),
        ('offer_letter', 'Offer Letter'),
        ('joining_letter', 'Joining Letter'),
        ('contract', 'Employment Contract'),
        ('id_proof', 'ID Proof'),
        ('address_proof', 'Address Proof'),
        ('educational_certificate', 'Educational Certificate'),
        ('experience_letter', 'Experience Letter'),
        ('salary_slip', 'Salary Slip'),
        ('appraisal', 'Appraisal Document'),
        ('warning', 'Warning Letter'),
        ('termination', 'Termination Letter'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='documents'
    )

    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    file = models.FileField(
        upload_to='employee_documents/%Y/%m/%d/',
        max_length=500
    )
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_document_type_display()}"


class EmployeeMedia(models.Model):
    MEDIA_TYPES = [
        ('profile_picture', 'Profile Picture'),
        ('id_photo', 'ID Photo'),
        ('id_card_photo', 'ID Card Photo'),
        ('signature', 'Signature'),
        ('work_sample', 'Work Sample'),
        ('training_certificate', 'Training Certificate'),
        ('award_certificate', 'Award Certificate'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='media_files'
    )

    media_type = models.CharField(max_length=50, choices=MEDIA_TYPES)
    file = models.FileField(
        upload_to='employee_media/%Y/%m/%d/',
        max_length=500
    )
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Employee Media'
        verbose_name_plural = 'Employee Media'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_media_type_display()}"


class SalaryPayment(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('early_paid', 'Early Paid'),
        ('overdue', 'Overdue'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('upi', 'UPI'),
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('other', 'Other'),
    ]

    employee = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='salary_payments'
    )
    
    month = models.IntegerField()
    year = models.IntegerField()
    
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    incentives = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    scheduled_date = models.DateField()
    
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
        CustomUser,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='processed_salary_payments'
    )

    remarks = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Salary Payment Record'
        verbose_name_plural = 'Salary Payment Records'
        unique_together = ('employee', 'month', 'year')
        ordering = ['-year', '-month']
    
    def __str__(self):
        return f"{self.employee.username} - {self.month}/{self.year} ({self.status})"

    def save(self, *args, **kwargs):
        
        if self.net_amount is None or not self.pk:
            self.net_amount = self.base_salary + self.incentives - self.deductions
        super().save(*args, **kwargs)


class CameraDepartment(models.Model):

    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
        ('urgent', 'Urgent'),
    ]
    file_path = models.CharField(
        max_length=500, 
        help_text="Path to the file on local system/network",
        default="not uploaded",
    )

    employee = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='camera_department_projects',
        blank=True,
        null=True
    )

    client = models.ForeignKey(
        'clientapp.Client',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='camera_department_projects'
    )

    uploaded_date = models.DateField(default=timezone.now)
    priority = models.CharField(
        max_length=20, 
        choices=PRIORITY_CHOICES, 
        default='medium' 
    )

    link = models.URLField(
        blank=True, 
        null=True, 
        
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Camera Department Project'
        verbose_name_plural = 'Camera Department Projects'
        ordering = ['-uploaded_date']

    def __str__(self):
        return f"{self.client.client_name} - Project ({self.uploaded_date})"


class LeaveManagement(models.Model):

    LEAVE_CATEGORY_CHOICES = [
        ('Annual Leave', 'Annual Leave'),
        ('Sick Leave', 'Sick Leave'),
        ('Casual Leave', 'Casual Leave'),
        ('Bereavement Leave', 'Bereavement Leave'),
        ('LOP', 'Leave Without Pay (LOP)'),
        ('WFH', 'Work From Home (WFH)'),
        ('Other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]


    employee = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='leaves'
    )
    
    category = models.CharField(
        max_length=20,
        choices=LEAVE_CATEGORY_CHOICES,
        verbose_name="Category of Leave"
    ) 
    
    start_date = models.CharField(max_length=100)  
    end_date = models.CharField(max_length=100) 

    total_days = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        validators=[MinValueValidator(Decimal('0.5'))],
        verbose_name="Total Number of Leave Days"
    )
    
    reason = models.TextField(
        verbose_name="Reason for the Leave",
        blank=True,
        null=True
    )
    
    address_during_leave = models.TextField(
        blank=True,
        null=True,
        verbose_name="Address During Leave"
    )

    attachment = models.FileField(
        upload_to='leave_attachments/',
        blank=True,
        null=True,
        verbose_name="Attach Media"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='approved_leave_applications',
        limit_choices_to={'role': 'manager'}
    )
    
    approved_at = models.DateTimeField(
        blank=True,
        null=True
    )
    
    remarks = models.TextField(
        blank=True,
        null=True
    )
    
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Leave Application"
        verbose_name_plural = "Leave Applications"
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.category} ({self.start_date} to {self.end_date})"


class LeaveBalance(models.Model):
    employee = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='leave_balance'
    )
    annual_total = models.DecimalField(max_digits=5, decimal_places=1, default=18.0)
    casual_total = models.DecimalField(max_digits=5, decimal_places=1, default=12.0)
    sick_total = models.DecimalField(max_digits=5, decimal_places=1, default=6.0)
    year = models.IntegerField(default=timezone.now().year)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Leave Balance"
        verbose_name_plural = "Leave Balances"
        unique_together = ('employee', 'year')

    def __str__(self):
        return f"{self.employee.employee_id} - {self.year} Balance"




