from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal

class LeaveApplication(models.Model):
    LEAVE_TYPE_CHOICES = [
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
        ('active', 'Active'),
        ('upcoming', 'Upcoming'),
    ]

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='leaves_new_admin'
    )
    leave_type = models.CharField(max_length=50, choices=LEAVE_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.DecimalField(max_digits=5, decimal_places=1)
    reason = models.TextField()
    address_during_leave = models.TextField(blank=True, null=True)
    passport_required_from = models.CharField(max_length=100, blank=True, null=True)
    passport_required_to = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_date = models.DateTimeField(auto_now_add=True)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='approved_leaves_new_admin'
    )
    approved_at = models.DateTimeField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to='leave_attachments/', blank=True, null=True)

    class Meta:
        ordering = ['-applied_date']
        verbose_name = "Admin Leave Application"
        verbose_name_plural = "Admin Leave Applications"

    def __str__(self):
        return f"{self.employee.username} - {self.leave_type} ({self.start_date} to {self.end_date})"
