from django.utils import timezone
from datetime import date
import calendar

def calculate_next_payment_date(client):
    today = timezone.now().date()
    
    current_year = today.year
    current_month = today.month
    
    _, last_day_current_month = calendar.monthrange(current_year, current_month)
    adjusted_payment_date = min(client.payment_date, last_day_current_month)
    
    current_month_payment_date = date(current_year, current_month, adjusted_payment_date)
    
    if today <= current_month_payment_date:
        client.next_payment_date = current_month_payment_date
    else:
        if current_month == 12:
            next_year = current_year + 1
            next_month = 1
        else:
            next_year = current_year
            next_month = current_month + 1
        
        _, last_day_next_month = calendar.monthrange(next_year, next_month)
        adjusted_payment_date_next = min(client.payment_date, last_day_next_month)
        
        client.next_payment_date = date(next_year, next_month, adjusted_payment_date_next)

def update_payment_status(client):
    today = timezone.now().date()
    
    if client.current_month_payment_status in ['paid', 'early_paid']:
        return
    
    if client.next_payment_date:
        if today >= client.next_payment_date:
            client.current_month_payment_status = 'overdue'
        else:
            client.current_month_payment_status = 'pending'

def mark_payment_as_paid(client, payment_date=None, amount=None, notes=None):
    today = payment_date or timezone.now().date()
    client.current_month_payment_status = 'paid'
    client.last_payment_date = today
    if client.next_payment_date:
        if today < client.next_payment_date:
            client.payment_timing = 'early'
            client.current_month_payment_status = 'early_paid'
        elif today == client.next_payment_date:
            client.payment_timing = 'on_time'
        else:
            client.payment_timing = 'late'
    else:
        client.payment_timing = 'on_time'
    
    calculate_next_payment_date_after_payment(client)
    
    client.save()

def calculate_next_payment_date_after_payment(client):
    today = client.last_payment_date or timezone.now().date()
    
    if client.payment_cycle == 'monthly':
        if today.month == 12:
            next_year = today.year + 1
            next_month = 1
        else:
            next_year = today.year
            next_month = today.month + 1
        _, last_day_next_month = calendar.monthrange(next_year, next_month)
        adjusted_payment_date = min(client.payment_date, last_day_next_month)
        
        client.next_payment_date = date(next_year, next_month, adjusted_payment_date)
        
    elif client.payment_cycle == 'quarterly':
        next_month = today.month + 3
        next_year = today.year
        if next_month > 12:
            next_month -= 12
            next_year += 1
        
        _, last_day_next_quarter = calendar.monthrange(next_year, next_month)
        adjusted_payment_date = min(client.payment_date, last_day_next_quarter)
        
        client.next_payment_date = date(next_year, next_month, adjusted_payment_date)
        
    elif client.payment_cycle == 'yearly':
        next_year = today.year + 1
        _, last_day_next_year = calendar.monthrange(next_year, today.month)
        adjusted_payment_date = min(client.payment_date, last_day_next_year)
        
        client.next_payment_date = date(next_year, today.month, adjusted_payment_date)
