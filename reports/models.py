from django.db import models
from django.conf import settings


class MonthlyEmployeeReport(models.Model):
    """
    Stores a historical snapshot of a monthly employee report.
    """
    month = models.IntegerField()
    year = models.IntegerField()
    
    total_base_salary = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_incentives = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_net_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_leave_days = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expected_salary = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    employee_count = models.IntegerField(default=0)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_employee_reports'
    )

    class Meta:
        unique_together = ('month', 'year')
        ordering = ['-year', '-month']

    def __str__(self):
        import calendar
        return f"{calendar.month_name[self.month]} {self.year} Employee Report"

class MonthlyClientReport(models.Model):
    """
    Stores a historical snapshot of a monthly client report.
    """
    month = models.IntegerField()
    year = models.IntegerField()
    
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_discount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    expected_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    client_count = models.IntegerField(default=0)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_client_reports'
    )

    class Meta:
        unique_together = ('month', 'year')
        ordering = ['-year', '-month']

    def __str__(self):
        import calendar
        return f"{calendar.month_name[self.month]} {self.year} Client Report"

class MonthlyExpenseReport(models.Model):
    """
    Stores a historical snapshot of a monthly expense report.
    """
    month = models.IntegerField()
    year = models.IntegerField()
    
    total_expense = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    expense_count = models.IntegerField(default=0)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_expense_reports'
    )

    class Meta:
        unique_together = ('month', 'year')
        ordering = ['-year', '-month']

    def __str__(self):
        import calendar
        return f"{calendar.month_name[self.month]} {self.year} Expense Report"

class MonthlyIncomeReport(models.Model):
    """
    Stores a historical snapshot of a monthly income report.
    """
    month = models.IntegerField()
    year = models.IntegerField()
    
    total_income = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    income_count = models.IntegerField(default=0)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_income_reports'
    )

    class Meta:
        unique_together = ('month', 'year')
        ordering = ['-year', '-month']

    def __str__(self):
        import calendar
        return f"{calendar.month_name[self.month]} {self.year} Income Report"