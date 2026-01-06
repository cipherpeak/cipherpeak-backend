# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone

class CustomUser(AbstractUser):
    # Role Choices
    ROLE_CHOICES = [
        ('superuser', 'Superuser'),
        ('admin', 'Admin'),
        ('employee', 'Employee'),
    ]

    # User Type Choices (Specific roles for employees)
    USER_TYPE_CHOICES = [
        ('developer', 'Developer'),
        ('camera_department', 'Camera Department'),
        ('editor', 'Editor'),
        ('marketer', 'Marketer'),
        ('hr', 'HR'),
        ('manager', 'Manager'),
        ('content_creator', 'Content Creator'),
    ]
    
    # Status Choices
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('on_leave', 'On Leave'),
        ('probation_period', 'Probation Period'),
        ('notice_period', 'Notice Period'),
        ('inactive', 'Inactive'),
        ('terminated', 'Terminated'),
    ]
    
    # Existing fields
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
    
    # Emergency contact information
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True, null=True)
    
    # Address information
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    
    # Additional personal information
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
    
    # Employment details
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
        return f"{self.user.username} - {self.get_document_type_display()} - {self.title}"

class EmployeeMedia(models.Model):
    MEDIA_TYPES = [
        ('profile_picture', 'Profile Picture'),
        ('id_photo', 'ID Photo'),
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
        return f"{self.user.username} - {self.get_media_type_display()} - {self.title}"

class LeaveRecord(models.Model):
    LEAVE_TYPES = [
        ('sick', 'Sick Leave'),
        ('casual', 'Casual Leave'),
        ('earned', 'Earned Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('bereavement', 'Bereavement Leave'),
        ('other', 'Other Leave'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='leave_records'
    )
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_on = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_leaves'
    )
    approved_on = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.leave_type} - {self.start_date} to {self.end_date}"

class SalaryHistory(models.Model):

    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='salary_history'
    )
    salary = models.DecimalField(max_digits=12, decimal_places=2)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    reason = models.CharField(max_length=200, blank=True, null=True)
    changed_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='salary_changes'
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Salary History'
        verbose_name_plural = 'Salary History'
        ordering = ['-effective_from']
    
    def __str__(self):
        return f"{self.user.username} - {self.salary} - from {self.effective_from}"

class CameraDepartment(models.Model):
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
        ('urgent', 'Urgent'),
    ]

    client = models.ForeignKey(
        'clientapp.Client',
        on_delete=models.CASCADE,
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