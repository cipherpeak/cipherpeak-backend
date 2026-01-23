# models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal

User = get_user_model()

class TimeStampedModel(models.Model):
    """Abstract base model with created and updated timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class IncomeCategory(models.Model):
    """Model for income categories"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Income Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class ExpenseCategory(models.Model):
    """Model for expense categories"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Expense Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Income(TimeStampedModel):
    """Model for income records"""
    
    # Constants for choices
    INCOME_TYPES = [
        ('client_payment', 'Client Payment'),
        ('consulting_fee', 'Consulting Fee'),
        ('product_sale', 'Product Sale'),
        ('subscription_revenue', 'Subscription Revenue'),
        ('investment_return', 'Investment Return'),
        ('other_income', 'Other Income'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('credit_card', 'Credit Card'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('digital_wallet', 'Digital Wallet'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    type = models.CharField(max_length=50, choices=INCOME_TYPES)
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    gst_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    gst_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    category = models.ForeignKey(
        IncomeCategory, 
        on_delete=models.PROTECT,
        related_name='incomes'
    )
    date = models.DateField()
    
    # Client Information
    client_name = models.CharField(max_length=255, blank=True, null=True)
    client_email = models.EmailField(blank=True, null=True)
    client_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Additional Details
    remarks = models.TextField(blank=True, null=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    is_recurring = models.BooleanField(default=False)
    recurring_frequency = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        choices=[
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly'),
        ]
    )
    
    # Payment Information
    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        default='bank_transfer'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='completed'
    )
    
    # File Attachment
    attachment = models.FileField(
        upload_to='income_attachments/%Y/%m/%d/',
        blank=True,
        null=True
    )
    
    # Audit Fields
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_incomes'
    )
    last_modified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='modified_incomes'
    )
    
    def save(self, *args, **kwargs):
        if self.total_amount is None or self.total_amount == 0:
            self.total_amount = self.amount + self.gst_amount
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Income"
        verbose_name_plural = "Incomes"
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['type']),
            models.Index(fields=['category']),
            models.Index(fields=['payment_status']),
        ]
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.amount} - {self.date}"
    
    def get_type_display(self):
        """Get human-readable type display"""
        return dict(self.INCOME_TYPES).get(self.type, self.type)
    
    def get_payment_status_display(self):
        """Get human-readable payment status display"""
        return dict(self.PAYMENT_STATUS_CHOICES).get(self.payment_status, self.payment_status)
    
    def get_payment_method_display(self):
        """Get human-readable payment method display"""
        return dict(self.PAYMENT_METHOD_CHOICES).get(self.payment_method, self.payment_method)
    
    @property
    def formatted_amount(self):
        return f"${self.amount:,.2f}"

class Expense(TimeStampedModel):
    """Model for expense records"""
    
    # Constants for choices
    EXPENSE_TYPES = [
        ('software_subscription', 'Software Subscription'),
        ('office_rent', 'Office Rent'),
        ('utilities', 'Utilities'),
        ('marketing', 'Marketing'),
        ('business_travel', 'Business Travel'),
        ('equipment_purchase', 'Equipment Purchase'),
        ('employee_salaries', 'Employee Salaries'),
        ('office_supplies', 'Office Supplies'),
        ('professional_services', 'Professional Services'),
        ('other_expense', 'Other Expense'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('credit_card', 'Credit Card'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('digital_wallet', 'Digital Wallet'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    type = models.CharField(max_length=50, choices=EXPENSE_TYPES)
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    category = models.ForeignKey(
        ExpenseCategory, 
        on_delete=models.PROTECT,
        related_name='expenses'
    )
    date = models.DateField()
    
    # Vendor Information
    vendor_name = models.CharField(max_length=255, blank=True, null=True)
    vendor_contact = models.CharField(max_length=255, blank=True, null=True)
    vendor_email = models.EmailField(blank=True, null=True)
    vendor_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Additional Details
    remarks = models.TextField(blank=True, null=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    is_recurring = models.BooleanField(default=False)
    recurring_frequency = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        choices=[
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly'),
        ]
    )
    
    # Payment Information
    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        default='bank_transfer'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='completed'
    )
    
    # File Attachment
    receipt = models.FileField(
        upload_to='expense_receipts/%Y/%m/%d/',
        blank=True,
        null=True
    )
    
    # Audit Fields
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_expenses'
    )
    last_modified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='modified_expenses'
    )
    
    class Meta:
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['type']),
            models.Index(fields=['category']),
            models.Index(fields=['payment_status']),
        ]
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.amount} - {self.date}"
    
    def get_type_display(self):
        """Get human-readable type display"""
        return dict(self.EXPENSE_TYPES).get(self.type, self.type)
    
    def get_payment_status_display(self):
        """Get human-readable payment status display"""
        return dict(self.PAYMENT_STATUS_CHOICES).get(self.payment_status, self.payment_status)
    
    def get_payment_method_display(self):
        """Get human-readable payment method display"""
        return dict(self.PAYMENT_METHOD_CHOICES).get(self.payment_method, self.payment_method)
    
    @property
    def formatted_amount(self):
        return f"${self.amount:,.2f}"

class FinancialSummary(models.Model):
    """Model to store periodic financial summaries"""
    
    PERIOD_TYPE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    period_type = models.CharField(
        max_length=10,
        choices=PERIOD_TYPE_CHOICES
    )
    period_start = models.DateField()
    period_end = models.DateField()
    
    total_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Counts
    income_count = models.PositiveIntegerField(default=0)
    expense_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Financial Summaries"
        unique_together = ['period_type', 'period_start', 'period_end']
        ordering = ['-period_start']
    
    def get_period_type_display(self):
        """Get human-readable period type display"""
        return dict(self.PERIOD_TYPE_CHOICES).get(self.period_type, self.period_type)
    
    def __str__(self):
        return f"{self.period_type} Summary - {self.period_start} to {self.period_end}"