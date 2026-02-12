from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date
import calendar
from finance.models import Income, Expense
from clientapp.models import ClientPayment
from emplyees.models import SalaryPayment, LeaveManagement
from task.models import Task
from verification.models import ClientVerification

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
            # Attempt to parse dates with more flexibility
            # Handles 'YYYY-MM-DD', 'YYYY-MM-DDTHH:MM:SS', etc.
            start_str = l.start_date[:10]
            end_str = l.end_date[:10]
            
            l_start = datetime.strptime(start_str, '%Y-%m-%d').date()
            l_end = datetime.strptime(end_str, '%Y-%m-%d').date()
            
            # Check for overlap
            if l_start <= month_end and l_end >= month_start:
                monthly_leaves.append({
                    'employee_id': l.employee.id,
                    'employee_name': l.employee.get_full_name() or l.employee.username,
                    'category': l.category,
                    'start_date': l.start_date,
                    'end_date': l.end_date,
                    'total_days': float(l.total_days),
                    'status': l.get_status_display(),
                    'status_code': l.status,
                    'reason': l.reason
                })
        except (ValueError, TypeError, IndexError):
            continue

    return {
        'details': monthly_leaves,
        'summary': {
            'count': len(monthly_leaves),
            'total_days': sum(l['total_days'] for l in monthly_leaves if l['status_code'] == 'approved')
        }
    }

def get_monthly_client_data(month, year):
    """
    Fetches and aggregates all client revenue data for a given month and year.
    Iterates over ALL active clients, attaching payment info if available.
    """
    from verification.models import ClientVerification
    from clientapp.models import Client, ClientPayment
    
    # Get all active clients
    clients = Client.objects.filter(is_deleted=False).exclude(status='terminated')
    
    client_data = []
    total_revenue = 0
    total_tax = 0
    total_discount = 0
    total_expected_revenue = 0
    
    # Prefetch payments for this batch of clients for this month/year to avoid N+1
    # We can do this efficiently by filtering payments
    payments = ClientPayment.objects.filter(
        month=month,
        year=year,
        status__in=['paid', 'early_paid', 'partial'],
        client__in=clients
    ).select_related('client')
    
    # Create valid payment map: client_id -> payment_obj
    payment_map = {p.client.id: p for p in payments}

    for client in clients:
        try:
            # Auto-calculate expected revenue
            total_expected_revenue += client.monthly_retainer or 0

            # Get verified content counts for this month from MonthlyVerification
            from verification.models import MonthlyVerification
            
            # Since each client has a single ClientVerification record
            cv = ClientVerification.objects.filter(client=client).first()
            monthly_stat = None
            if cv:
                monthly_stat = MonthlyVerification.objects.filter(
                    clientverification=cv,
                    month=month,
                    year=year
                ).first()
            
            counts_dict = {
                'video': monthly_stat.videos_completed if monthly_stat else 0,
                'poster': monthly_stat.posters_completed if monthly_stat else 0,
                'reels': 0, # Future: Add these to MonthlyVerification if needed
                'stories': 0,
            }

            # Check if there is a payment
            cp = payment_map.get(client.id)
            
            # Default values if no payment
            amount = 0
            tax_amount = 0
            discount = 0
            net_amount = 0
            payment_date = None
            payment_method_display = 'N/A'
            transaction_id = 'N/A'
            status = 'Pending' # Or 'Unpaid'
            remarks = ''

            if cp:
                amount = cp.amount
                tax_amount = cp.tax_amount
                discount = cp.discount
                net_amount = cp.net_amount
                payment_date = cp.payment_date.strftime('%Y-%m-%d') if cp.payment_date else None
                
                if hasattr(cp, 'payment_method') and cp.payment_method:
                    try:
                        payment_method_display = cp.get_payment_method_display()
                    except:
                        payment_method_display = str(cp.payment_method)
                
                transaction_id = getattr(cp, 'transaction_id', None) or 'N/A'
                status = cp.get_status_display() if hasattr(cp, 'get_status_display') else 'N/A'
                remarks = getattr(cp, 'remarks', '') or ''
                
                # Accumulate totals only if payment exists
                total_revenue += net_amount
                total_tax += tax_amount
                total_discount += discount
            else:
                 # Check if the client has a payment record that is NOT paid (e.g. pending/overdue)
                 # This is optional but gives better status visibility
                 pending_cp = ClientPayment.objects.filter(
                    client=client,
                    month=month,
                    year=year
                 ).first()
                 if pending_cp:
                     status = pending_cp.get_status_display()
            

            client_data.append({
                'id': client.id,
                'client_name': getattr(client, 'client_name', 'N/A'),
                'industry': getattr(client, 'industry', 'N/A'),
                'location': getattr(client, 'city', 'N/A'),
                'monthly_retainer': getattr(client, 'monthly_retainer', 0),
                'payment_cycle': client.get_payment_cycle_display() if hasattr(client, 'get_payment_cycle_display') else 'N/A',
                'tax_id': getattr(client, 'tax_id', 'N/A') or 'N/A',
                'owner_name': getattr(client, 'owner_name', 'N/A') or 'N/A',
                'contact_person': getattr(client, 'contact_person_name', 'N/A') or 'N/A',
                'contact_email': getattr(client, 'contact_email', 'N/A') or 'N/A',
                'contact_phone': getattr(client, 'contact_phone', 'N/A') or 'N/A',
                'content_requirements': {
                    'videos': {'target': getattr(client, 'videos_per_month', 0) or 0, 'actual': counts_dict.get('video', 0)},
                    'posters': {'target': getattr(client, 'posters_per_month', 0) or 0, 'actual': counts_dict.get('poster', 0)},
                    'reels': {'target': getattr(client, 'reels_per_month', 0) or 0, 'actual': counts_dict.get('reel', 0)},
                    'stories': {'target': getattr(client, 'stories_per_month', 0) or 0, 'actual': counts_dict.get('story', 0)},
                },
                'amount': amount,
                'tax': tax_amount,
                'discount': discount,
                'net_amount': net_amount,
                'payment_date': payment_date,
                'payment_method': payment_method_display,
                'transaction_id': transaction_id,
                'status': status,
                'remarks': remarks
            })
        except Exception as e:
            # Log the error but continue processing other clients
            print(f"Error processing client {client.id}: {str(e)}")
        

    # Fetch Tasks for these clients in this period
    tasks = Task.objects.filter(
        created_at__month=month,
        created_at__year=year,
        is_deleted=False
    ).select_related('client', 'assignee')

    return {
        'details': client_data,
        'tasks': [{
            'title': t.title,
            'client': t.client.client_name if t.client else 'N/A',
            'assignee': t.assignee.get_full_name() or t.assignee.username,
            'status': t.get_status_display(),
            'created_at': t.created_at.strftime('%Y-%m-%d')
        } for t in tasks],
        'summary': {
            'total_revenue': total_revenue,
            'total_tax': total_tax,
            'total_discount': total_discount,
            'total_expected_revenue': total_expected_revenue,
            'count': len(client_data),
            'task_count': tasks.count()
        }
    }

def get_monthly_employee_data(month, year):
    """
    Fetches and aggregates all employee salary data for a given month and year.
    Iterates over ALL active employees, attaching salary info if available.
    """
    from emplyees.models import CustomUser
    
    # Fetch all active employees (excluding superusers if desired, or based on role)
    # Assuming is_active=True is sufficient
    employees = CustomUser.objects.filter(is_active=True).exclude(is_superuser=True)
    
    salary_payments = SalaryPayment.objects.filter(
        month=month,
        year=year,
        status__in=['paid', 'early_paid'],
        employee__in=employees
    )
    
    # Map employee_id -> salary_payment
    salary_map = {sp.employee.id: sp for sp in salary_payments}

    employee_data = []
    total_salary = 0
    total_incentives = 0
    total_deductions = 0
    total_net = 0
    total_expected_salary = 0

    # Fetch leaves for these employees
    leave_report = get_monthly_leave_data(month, year)
    
    # Map leaves to employees for the details view if helpful
    employee_leaves = {}
    for l in leave_report['details']:
        emp_id = l['employee_id']
        if emp_id not in employee_leaves:
            employee_leaves[emp_id] = 0
        if l['status_code'] == 'approved':
            employee_leaves[emp_id] += l['total_days']

    for emp in employees:
        emp_name = emp.get_full_name() or emp.username
        
        # Auto-calculate expected salary
        total_expected_salary += emp.salary or 0

        # Calculate tasks for this SPECIFIC employee in this period
        emp_tasks = Task.objects.filter(
            assignee=emp,
            created_at__month=month,
            created_at__year=year,
            is_deleted=False
        )
        
        tasks_completed = emp_tasks.filter(status='completed').count()
        tasks_pending = emp_tasks.filter(status__in=['pending', 'in_progress', 'scheduled']).count()

        try:
            # Safely get gender display
            gender_display = 'N/A'
            if hasattr(emp, 'gender') and emp.gender:
                try:
                    gender_display = emp.get_gender_display()
                except:
                    gender_display = str(emp.gender) if emp.gender else 'N/A'
            
            # Safely get joining date
            joining_date_str = 'N/A'
            if hasattr(emp, 'joining_date') and emp.joining_date:
                try:
                    joining_date_str = emp.joining_date.strftime('%Y-%m-%d')
                except:
                    joining_date_str = str(emp.joining_date)
            
            # Get Salary Info if available
            sp = salary_map.get(emp.id)
            
            # Use employee's profile salary as default, fallback to 0
            default_base_salary = emp.salary if emp.salary else 0
            
            base_salary = default_base_salary
            incentives = 0
            deductions = 0
            net_paid = 0
            payment_date = None
            status = 'Unpaid'
            remarks = ''
            
            if sp:
                # If salary payment exists, use its values
                base_salary = sp.base_salary if sp.base_salary else default_base_salary
                incentives = sp.incentives
                deductions = sp.deductions
                net_paid = sp.net_amount
                payment_date = sp.payment_date.strftime('%Y-%m-%d') if sp.payment_date else None
                status = sp.get_status_display()
                remarks = sp.remarks or ''
                
                # Accumulate totals
                total_salary += base_salary
                total_incentives += incentives
                total_deductions += deductions
                total_net += net_paid
            
            employee_data.append({
                'id': emp.id,
                'employee_name': emp_name,
                'department': getattr(emp, 'department', None) or 'N/A',
                'designation': getattr(emp, 'designation', None) or 'Staff',
                'gender': gender_display,
                'email': getattr(emp, 'email', 'N/A'),
                'phone': getattr(emp, 'phone_number', None) or 'N/A',
                'joining_date': joining_date_str,
                'base_salary': base_salary,
                'incentives': incentives,
                'deductions': deductions,
                'net_paid': net_paid,
                'payment_date': payment_date,
                'status': status,
                'remarks': remarks,
                'leaves_count': employee_leaves.get(emp.id, 0),
                'tasks_completed': tasks_completed,
                'tasks_pending': tasks_pending
            })
        except Exception as e:
            # Log the error but continue processing other employees
            print(f"Error processing employee {emp.id}: {str(e)}")

    # Fetch Tasks assigned to employees for this period
    tasks = Task.objects.filter(
        created_at__month=month,
        created_at__year=year,
        is_deleted=False
    ).select_related('assignee', 'client')

    return {
        'details': employee_data,
        'tasks': [{
            'title': t.title,
            'assignee': t.assignee.get_full_name() or t.assignee.username,
            'client': t.client.client_name if t.client else 'N/A',
            'status': t.get_status_display(),
            'created_at': t.created_at.strftime('%Y-%m-%d')
        } for t in tasks],
        'leaves': leave_report,
        'summary': {
            'total_base_salary': total_salary,
            'total_incentives': total_incentives,
            'total_deductions': total_deductions,
            'total_net_paid': total_net,
            'total_expected_salary': total_expected_salary,
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
    import re

    def clean_remarks(remarks_text):
        if not remarks_text:
            return remarks_text
        # Remove "Salary Payment for [Name] - [Month] [Year]. "
        remarks_text = re.sub(r'Salary Payment for .*? - .*? \d{4}\.\s*', '', remarks_text)
        # Remove "Client Payment for [Month] [Year]. "
        remarks_text = re.sub(r'Client Payment for .*? \d{4}\.\s*', '', remarks_text)
        # Remove "Payment for [Month]/[Year]. " (older format potentially)
        remarks_text = re.sub(r'Payment for \d{1,2}/\d{4}\.\s*', '', remarks_text)
        return remarks_text

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
            'remarks': clean_remarks(inc.remarks)
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
            'remarks': clean_remarks(exp.remarks),
            'gst_amount': 0,
            'total_amount': exp.amount
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
