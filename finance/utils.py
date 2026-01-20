# finance/utils.py
from .models import Income, Expense, IncomeCategory, ExpenseCategory
from django.utils import timezone
from decimal import Decimal

def record_system_income(income_type, amount, date=None, category_name="General", client_name=None, client_email=None, client_phone=None, remarks=None, reference_number=None, payment_method='bank_transfer', created_by=None):
    """
    Utility to record system-generated income like client payments.
    """
    if not date:
        date = timezone.now().date()
    
    category, _ = IncomeCategory.objects.get_or_create(
        name=category_name,
        defaults={'description': f'System generated category for {category_name}'}
    )
    
    defaults = {
        'type': income_type,
        'amount': amount,
        'category': category,
        'date': date,
        'client_name': client_name,
        'client_email': client_email,
        'client_phone': client_phone,
        'remarks': remarks,
        'payment_method': payment_method,
        'payment_status': 'completed',
        'created_by': created_by
    }
    
    if reference_number:
        income, created = Income.objects.update_or_create(
            reference_number=reference_number,
            defaults=defaults
        )
    else:
        income = Income.objects.create(**defaults)
        
    return income

def record_system_expense(expense_type, amount, date=None, category_name="General", vendor_name=None, vendor_contact=None, remarks=None, reference_number=None, payment_method='bank_transfer', created_by=None):
    """
    Utility to record system-generated expenses like employee salaries.
    """
    if not date:
        date = timezone.now().date()
    
    category, _ = ExpenseCategory.objects.get_or_create(
        name=category_name,
        defaults={'description': f'System generated category for {category_name}'}
    )
    
    defaults = {
        'type': expense_type,
        'amount': amount,
        'category': category,
        'date': date,
        'vendor_name': vendor_name,
        'vendor_contact': vendor_contact,
        'remarks': remarks,
        'payment_method': payment_method,
        'payment_status': 'completed',
        'created_by': created_by
    }
    
    if reference_number:
        expense, created = Expense.objects.update_or_create(
            reference_number=reference_number,
            defaults=defaults
        )
    else:
        expense = Expense.objects.create(**defaults)
        
    return expense
