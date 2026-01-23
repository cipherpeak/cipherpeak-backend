from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date
import calendar
from finance.models import Income, Expense
from clientapp.models import ClientPayment
from emplyees.models import SalaryPayment, LeaveManagement
from task.models import Task

def get_monthly_leave_data(month, year):
    """
    Fetches all leave applications that overlap with the given month and year.
    """
    import calendar
    from datetime import datetime, date

    _, last_day = calendar.monthrange(year, month)
    month_start = date(year, month, 1)
    month_end = date(year, month, last_day)

    # Fetch all leaves. Since start_date/end_date are CharFields, we'll fetch more and filter in Python
    # OR if they are YYYY-MM-DD, we can use string comparison.
    # To be safe and since it's a reporting tool (not high frequency), we can filter in memory or try to use __gte/__lte if format is consistent.
    
    all_leaves = LeaveManagement.objects.all().select_related('employee')
    
    monthly_leaves = []
    
    for l in all_leaves:
        try:
            # Attempt to parse dates
            l_start = datetime.strptime(l.start_date[:10], '%Y-%m-%d').date()
            l_end = datetime.strptime(l.end_date[:10], '%Y-%m-%d').date()
            
            # Check for overlap
            if l_start <= month_end and l_end >= month_start:
                monthly_leaves.append({
                    'employee_name': l.employee.get_full_name() or l.employee.username,
                    'category': l.category,
                    'start_date': l.start_date,
                    'end_date': l.end_date,
                    'total_days': float(l.total_days),
                    'status': l.get_status_display(),
                    'reason': l.reason
                })
        except (ValueError, TypeError, IndexError):
            continue

    return {
        'details': monthly_leaves,
        'summary': {
            'count': len(monthly_leaves),
            'total_days': sum(l['total_days'] for l in monthly_leaves)
        }
    }

def get_monthly_client_data(month, year):
    """
    Fetches and aggregates all client revenue data for a given month and year.
    """
    from verification.models import ClientVerification
    
    payments = ClientPayment.objects.filter(
        month=month,
        year=year,
        status__in=['paid', 'early_paid', 'partial']
    ).select_related('client')

    client_data = []
    total_revenue = 0
    total_tax = 0
    total_discount = 0

    for cp in payments:
        # Get verified content counts for this month
        verified_counts = ClientVerification.objects.filter(
            client=cp.client,
            completion_date__month=month,
            completion_date__year=year
        ).values('content_type').annotate(count=Count('id'))
        
        counts_dict = {item['content_type']: item['count'] for item in verified_counts}

        client_data.append({
            'client_name': cp.client.client_name,
            'industry': cp.client.industry,
            'location': cp.client.city,
            'monthly_retainer': cp.client.monthly_retainer,
            'payment_cycle': cp.client.get_payment_cycle_display(),
            'tax_id': cp.client.tax_id,
            'owner_name': cp.client.owner_name,
            'contact_person': cp.client.contact_person_name,
            'contact_email': cp.client.contact_email,
            'contact_phone': cp.client.contact_phone,
            'content_requirements': {
                'videos': {'target': cp.client.videos_per_month, 'actual': counts_dict.get('video', 0)},
                'posters': {'target': cp.client.posters_per_month, 'actual': counts_dict.get('poster', 0)},
                'reels': {'target': cp.client.reels_per_month, 'actual': counts_dict.get('reel', 0)},
                'stories': {'target': cp.client.stories_per_month, 'actual': counts_dict.get('story', 0)},
            },
            'amount': cp.amount,
            'tax': cp.tax_amount,
            'discount': cp.discount,
            'net_amount': cp.net_amount,
            'payment_date': cp.payment_date.strftime('%Y-%m-%d') if cp.payment_date else None,
            'payment_method': cp.get_payment_method_display() if cp.payment_method else 'N/A',
            'transaction_id': cp.transaction_id or 'N/A',
            'status': cp.get_status_display(),
            'remarks': cp.remarks
        })
        total_revenue += cp.net_amount
        total_tax += cp.tax_amount
        total_discount += cp.discount

    # Fetch Tasks for these clients in this period
    tasks = Task.objects.filter(
        due_date__month=month,
        due_date__year=year,
        is_deleted=False
    ).select_related('client', 'assignee')

    return {
        'details': client_data,
        'tasks': [{
            'title': t.title,
            'client': t.client.client_name if t.client else 'N/A',
            'assignee': t.assignee.get_full_name() or t.assignee.username,
            'status': t.get_status_display(),
            'due_date': t.due_date.strftime('%Y-%m-%d')
        } for t in tasks],
        'summary': {
            'total_revenue': total_revenue,
            'total_tax': total_tax,
            'total_discount': total_discount,
            'count': len(client_data),
            'task_count': tasks.count()
        }
    }

def get_monthly_employee_data(month, year):
    """
    Fetches and aggregates all employee salary data for a given month and year.
    """
    payments = SalaryPayment.objects.filter(
        month=month,
        year=year,
        status__in=['paid', 'early_paid']
    ).select_related('employee')

    employee_data = []
    total_salary = 0
    total_incentives = 0
    total_deductions = 0
    total_net = 0

    # Fetch leaves for these employees
    leave_report = get_monthly_leave_data(month, year)
    
    # Map leaves to employees for the details view if helpful
    employee_leaves = {}
    for l in leave_report['details']:
        emp_name = l['employee_name']
        if emp_name not in employee_leaves:
            employee_leaves[emp_name] = 0
        employee_leaves[emp_name] += l['total_days']

    for sp in payments:
        emp_name = sp.employee.get_full_name() or sp.employee.username
        employee_data.append({
            'employee_name': emp_name,
            'department': sp.employee.department if sp.employee.department else 'N/A',
            'base_salary': sp.base_salary,
            'incentives': sp.incentives,
            'deductions': sp.deductions,
            'net_paid': sp.net_amount,
            'payment_date': sp.payment_date.strftime('%Y-%m-%d') if sp.payment_date else None,
            'status': sp.get_status_display(),
            'leaves_count': employee_leaves.get(emp_name, 0)
        })
        total_salary += sp.base_salary
        total_incentives += sp.incentives
        total_deductions += sp.deductions
        total_net += sp.net_amount

    # Fetch Tasks assigned to employees for this period
    tasks = Task.objects.filter(
        due_date__month=month,
        due_date__year=year,
        is_deleted=False
    ).select_related('assignee', 'client')

    return {
        'details': employee_data,
        'tasks': [{
            'title': t.title,
            'assignee': t.assignee.get_full_name() or t.assignee.username,
            'client': t.client.client_name if t.client else 'N/A',
            'status': t.get_status_display(),
            'due_date': t.due_date.strftime('%Y-%m-%d')
        } for t in tasks],
        'leaves': leave_report,
        'summary': {
            'total_base_salary': total_salary,
            'total_incentives': total_incentives,
            'total_deductions': total_deductions,
            'total_net_paid': total_net,
            'count': len(employee_data),
            'task_count': tasks.count(),
            'total_leave_days': leave_report['summary']['total_days']
        }
    }

def get_monthly_general_data(month, year):
    """
    Fetches and aggregates general income and expenses (excluding system-generated ones covered above).
    """
    # Exclude client_payment type as it's covered by get_monthly_client_data
    incomes = Income.objects.filter(
        date__month=month,
        date__year=year
    ).exclude(type='client_payment')

    # Exclude employee_salaries type as it's covered by get_monthly_employee_data
    expenses = Expense.objects.filter(
        date__month=month,
        date__year=year
    ).exclude(type='employee_salaries')

    income_list = []
    total_general_income = 0
    for inc in incomes:
        income_list.append({
            'type': inc.get_type_display(),
            'category': inc.category.name,
            'amount': inc.amount,
            'date': inc.date.strftime('%Y-%m-%d'),
            'remarks': inc.remarks
        })
        total_general_income += inc.amount

    expense_list = []
    total_general_expense = 0
    for exp in expenses:
        expense_list.append({
            'type': exp.get_type_display(),
            'category': exp.category.name,
            'vendor': exp.vendor_name,
            'amount': exp.amount,
            'date': exp.date.strftime('%Y-%m-%d'),
            'remarks': exp.remarks
        })
        total_general_expense += exp.amount

    return {
        'income_details': income_list,
        'expense_details': expense_list,
        'summary': {
            'total_general_income': total_general_income,
            'total_general_expense': total_general_expense
        }
    }

def compile_full_monthly_report(month, year):
    """
    Combines all sections into a single comprehensive report.
    """
    client_report = get_monthly_client_data(month, year)
    employee_report = get_monthly_employee_data(month, year)
    general_report = get_monthly_general_data(month, year)

    total_income = client_report['summary']['total_revenue'] + general_report['summary']['total_general_income']
    total_expense = employee_report['summary']['total_net_paid'] + general_report['summary']['total_general_expense']
    net_profit = total_income - total_expense

    return {
        'month': month,
        'month_name': calendar.month_name[month],
        'year': year,
        'summary': {
            'total_income': total_income,
            'total_expense': total_expense,
            'net_profit': net_profit,
            'client_revenue': client_report['summary']['total_revenue'],
            'salary_outflow': employee_report['summary']['total_net_paid'],
            'operating_expenses': general_report['summary']['total_general_expense'],
            'tax_collected': client_report['summary']['total_tax'],
            'total_leave_days': employee_report['summary']['total_leave_days']
        },
        'client_details': client_report['details'],
        'employee_details': employee_report['details'],
        'tasks': client_report['tasks'],  # Combined tasks for the month
        'leave_details': employee_report['leaves']['details'],
        'general_transactions': {
            'income': general_report['income_details'],
            'expenses': general_report['expense_details']
        }
    }
def get_detailed_finance_data(month, year):
    """
    Fetches all income and expenses for a given month and year,
    including those generated by client payments and payroll.
    """
    incomes = Income.objects.filter(
        date__month=month,
        date__year=year
    ).select_related('category')

    expenses = Expense.objects.filter(
        date__month=month,
        date__year=year
    ).select_related('category')

    income_details = []
    total_income = 0
    for inc in incomes:
        income_details.append({
            'date': inc.date.strftime('%Y-%m-%d'),
            'type': inc.get_type_display(),
            'category': inc.category.name,
            'client_name': inc.client_name or 'N/A',
            'amount': inc.amount,
            'gst_amount': inc.gst_amount,
            'total_amount': inc.total_amount,
            'payment_method': inc.get_payment_method_display(),
            'status': inc.get_payment_status_display(),
            'remarks': inc.remarks
        })
        total_income += inc.total_amount

    expense_details = []
    total_expense = 0
    for exp in expenses:
        expense_details.append({
            'date': exp.date.strftime('%Y-%m-%d'),
            'type': exp.get_type_display(),
            'category': exp.category.name,
            'vendor_name': exp.vendor_name or 'N/A',
            'amount': exp.amount,
            'payment_method': exp.get_payment_method_display(),
            'status': exp.get_payment_status_display(),
            'remarks': exp.remarks
        })
        total_expense += exp.amount

    return {
        'month': month,
        'month_name': calendar.month_name[month],
        'year': year,
        'income': {
            'details': income_details,
            'total': total_income,
            'count': len(income_details)
        },
        'expense': {
            'details': expense_details,
            'total': total_expense,
            'count': len(expense_details)
        },
        'net_balance': total_income - total_expense
    }
