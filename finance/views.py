# finance/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import api_view, permission_classes
from django.db import models
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import date, datetime, timedelta
import calendar
from .models import Income, Expense, IncomeCategory, ExpenseCategory, FinancialSummary
from .serializers import (
    IncomeSerializer, 
    ExpenseSerializer,
    IncomeCategorySerializer,
    ExpenseCategorySerializer,
    IncomeListSerializer,
    ExpenseListSerializer,
    FinancialSummarySerializer
)
from clientapp.models import ClientPayment
from emplyees.models import SalaryPayment

class IncomeListCreateView(generics.ListCreateAPIView):
    """
    View for listing and creating income records
    """
    queryset = Income.objects.all()
    serializer_class = IncomeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        'type', 
        'client_name', 
        'remarks', 
        'reference_number',
        'category__name'
    ]
    ordering_fields = [
        'date', 
        'amount', 
        'created_at', 
        'type',
        'payment_status'
    ]
    ordering = ['-date', '-created_at']

    def get_queryset(self):
        """
        Optionally filter by type, category, payment_status, date range, or recurring
        """
        queryset = Income.objects.exclude(type='client_payment')
        
        # Filter by income type
        income_type = self.request.query_params.get('type', None)
        if income_type:
            queryset = queryset.filter(type=income_type)
            
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category_id=category)
            
        # Filter by payment status
        payment_status = self.request.query_params.get('payment_status', None)
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)
            
        # Filter by payment method
        payment_method = self.request.query_params.get('payment_method', None)
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
            
        # Filter recurring income
        recurring = self.request.query_params.get('recurring', None)
        if recurring and recurring.lower() == 'true':
            queryset = queryset.filter(is_recurring=True)
            
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__gte=start_date)
            except ValueError:
                pass
                
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__lte=end_date)
            except ValueError:
                pass
            
        return queryset

    def get_serializer_class(self):
        """Use different serializer for list vs create"""
        if self.request.method == 'GET':
            return IncomeListSerializer
        return IncomeSerializer

    def perform_create(self, serializer):
        """Set the created_by user when creating income"""
        serializer.save(created_by=self.request.user)

    def list(self, request, *args, **kwargs):
        # 1. Get standard Incomes
        queryset = self.filter_queryset(self.get_queryset())
        income_data = self.get_serializer(queryset, many=True).data
        
        # 2. Get Client Payments
        client_payments = ClientPayment.objects.filter(
            status__in=['paid', 'early_paid', 'partial']
        )
        
        # Apply date filters
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                client_payments = client_payments.filter(payment_date__date__gte=start_dt)
            except ValueError: pass
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                client_payments = client_payments.filter(payment_date__date__lte=end_dt)
            except ValueError: pass
            
        # 3. Transform and Merge
        payment_data = []
        for cp in client_payments:
            eff_date = cp.payment_date.date() if cp.payment_date else cp.scheduled_date
            payment_item = {
                'id': 1000000 + cp.id,
                'type': 'client_payment',
                'type_display': 'Client Payment',
                'amount': str(cp.net_amount),
                'formatted_amount': f"${cp.net_amount:,.2f}",
                'gst_amount': str(cp.tax_amount),
                'gst_rate': '0.00',
                'total_amount': str(cp.net_amount),
                'category': 0,
                'category_name': 'Client Payment',
                'date': eff_date.strftime('%Y-%m-%d'),
                'client_name': cp.client.client_name,
                'remarks': cp.remarks,
                'reference_number': f"CP-{cp.id}",
                'is_recurring': False,
                'recurring_frequency': None,
                'payment_method': cp.payment_method or 'bank_transfer',
                'payment_method_display': cp.get_payment_method_display() if cp.payment_method else 'Bank Transfer',
                'payment_status': 'completed' if cp.status in ['paid', 'early_paid'] else cp.status,
                'payment_status_display': 'Completed',
                'created_by': cp.processed_by.id if cp.processed_by else None,
                'created_by_name': cp.processed_by.get_full_name() if cp.processed_by else 'System',
                'created_at': cp.created_at,
            }
            payment_data.append(payment_item)
            
        combined_data = income_data + payment_data
        combined_data.sort(key=lambda x: x['date'], reverse=True)
        return Response(combined_data)



class ClientPaymentWrapper:
    """Wrapper to make ClientPayment look like Income for the serializer"""
    def __init__(self, payment):
        self._payment = payment
        self.id = 1000000 + payment.id
        self.type = 'client_payment'
        self.amount = payment.net_amount
        self.gst_amount = payment.tax_amount
        self.gst_rate = 0
        self.total_amount = payment.net_amount
        self.date = payment.payment_date.date() if payment.payment_date else payment.scheduled_date
        
        # Client info
        self.client_name = payment.client.client_name
        self.client_email = payment.client.contact_email
        self.client_phone = payment.client.contact_phone
        
        self.remarks = payment.remarks
        self.reference_number = f"CP-{payment.id}"
        
        # Recurring - Defaults
        self.is_recurring = False
        self.recurring_frequency = None
        
        # Payment info
        self.payment_method = payment.payment_method or 'bank_transfer'
        
        # Map generic status to income status
        if payment.status in ['paid', 'early_paid']:
            self.payment_status = 'completed'
        elif payment.status == 'partial':
            self.payment_status = 'pending' # Or partial if supported
        else:
            self.payment_status = payment.status
            
        self.attachment = None
        self.created_by = payment.processed_by
        self.last_modified_by = payment.processed_by
        self.created_at = payment.created_at
        self.updated_at = payment.updated_at
        
        # Mock Category
        class CategoryMock:
            name = 'Client Payment'
            id = 0
            def __str__(self): return 'Client Payment'
        self.category = CategoryMock()

    def get_type_display(self):
        return 'Client Payment'
    
    def get_payment_status_display(self):
        # Return mapped status display
        status_map = {
            'pending': 'Pending',
            'completed': 'Completed',
            'failed': 'Failed',
            'refunded': 'Refunded'
        }
        return status_map.get(self.payment_status, self.payment_status)
    
    def get_payment_method_display(self):
        return self._payment.get_payment_method_display() if self._payment.payment_method else 'Bank Transfer'
    
    @property
    def formatted_amount(self):
        return f"${self.amount:,.2f}"
        
    @property
    def pk(self):
        return self.id

class IncomeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View for retrieving, updating and deleting a specific income record
    """
    queryset = Income.objects.all()
    serializer_class = IncomeSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_object(self):
        """
        Override to handle both Income and ClientPayment details
        """
        lookup_url_kwarg = self.lookup_field
        lookup = self.kwargs.get(lookup_url_kwarg)
        
        try:
            income_id = int(lookup)
            # Check if this is a Client Payment (ID > 1000000)
            if income_id > 1000000:
                cp_id = income_id - 1000000
                try:
                    client_payment = ClientPayment.objects.get(id=cp_id)
                    return ClientPaymentWrapper(client_payment)
                except ClientPayment.DoesNotExist:
                    from django.http import Http404
                    raise Http404("Client Payment not found")
        except (ValueError, TypeError):
            pass
            
        return super().get_object()

    def perform_update(self, serializer):
        """Set the last_modified_by user when updating income"""
        # Note: formatting updates for Client Payments (via wrapper) might need special handling
        # Since serializer.save() calls instance.save(), the wrapper needs a save method 
        # or we block updates here.
        if isinstance(serializer.instance, ClientPaymentWrapper):
            # For now, we don't support updating Client Payments via this endpoint
            # to avoid data inconsistency.
            # Use ClientPayment-specific endpoints for updates.
            return
            
        serializer.save(last_modified_by=self.request.user)

class ExpenseListCreateView(generics.ListCreateAPIView):
    """
    View for listing and creating expense records
    """
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        'type', 
        'vendor_name', 
        'remarks', 
        'reference_number',
        'category__name'
    ]
    ordering_fields = [
        'date', 
        'amount', 
        'created_at', 
        'type',
        'payment_status'
    ]
    ordering = ['-date', '-created_at']

    def get_queryset(self):
        """
        Optionally filter by type, category, payment_status, date range, or recurring
        """
        queryset = Expense.objects.exclude(type='employee_salaries')
        
        # Filter by expense type
        expense_type = self.request.query_params.get('type', None)
        if expense_type:
            queryset = queryset.filter(type=expense_type)
            
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category_id=category)
            
        # Filter by payment status
        payment_status = self.request.query_params.get('payment_status', None)
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)
            
        # Filter by payment method
        payment_method = self.request.query_params.get('payment_method', None)
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
            
        # Filter recurring expenses
        recurring = self.request.query_params.get('recurring', None)
        if recurring and recurring.lower() == 'true':
            queryset = queryset.filter(is_recurring=True)
            
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__gte=start_date)
            except ValueError:
                pass
                
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__lte=end_date)
            except ValueError:
                pass
            
        return queryset

    def get_serializer_class(self):
        """Use different serializer for list vs create"""
        if self.request.method == 'GET':
            return ExpenseListSerializer
        return ExpenseSerializer

    def list(self, request, *args, **kwargs):
        # 1. Get standard Expenses
        queryset = self.filter_queryset(self.get_queryset())
        expense_data = self.get_serializer(queryset, many=True).data
        
        # 2. Get Salary Payments
        salary_payments = SalaryPayment.objects.filter(
            status__in=['paid', 'early_paid', 'overdue']
        )
        
        # Apply date filters
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                salary_payments = salary_payments.filter(payment_date__date__gte=start_dt)
            except ValueError: pass
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                salary_payments = salary_payments.filter(payment_date__date__lte=end_dt)
            except ValueError: pass
            
        # 3. Transform and Merge
        payment_data = []
        for sp in salary_payments:
            eff_date = sp.payment_date.date() if sp.payment_date else sp.scheduled_date
            payment_item = {
                'id': 2000000 + sp.id,
                'type': 'employee_salaries',
                'type_display': 'Employee Salaries',
                'amount': str(sp.net_amount),
                'formatted_amount': f"${sp.net_amount:,.2f}",
                'category': 0,
                'category_name': 'Employee Salaries',
                'date': eff_date.strftime('%Y-%m-%d'),
                'vendor_name': sp.employee.get_full_name() or sp.employee.username,
                'remarks': sp.remarks,
                'reference_number': f"SAL-{sp.id}",
                'is_recurring': False,
                'recurring_frequency': None,
                'payment_method': sp.payment_method or 'bank_transfer',
                'payment_method_display': sp.get_payment_method_display() if sp.payment_method else 'Bank Transfer',
                'payment_status': 'completed' if sp.status in ['paid', 'early_paid'] else sp.status,
                'payment_status_display': sp.get_status_display(),
                'created_by': sp.processed_by.id if sp.processed_by else None,
                'created_by_name': sp.processed_by.get_full_name() if sp.processed_by else 'System',
                'created_at': sp.created_at,
            }
            payment_data.append(payment_item)
            
        combined_data = expense_data + payment_data
        combined_data.sort(key=lambda x: x['date'], reverse=True)
        return Response(combined_data)

class SalaryPaymentWrapper:
    """Wrapper to make SalaryPayment look like Expense for the serializer"""
    def __init__(self, payment):
        self._payment = payment
        self.id = 2000000 + payment.id
        self.type = 'employee_salaries'
        self.amount = payment.net_amount
        self.date = payment.payment_date.date() if payment.payment_date else payment.scheduled_date
        
        # Vendor info (the employee)
        self.vendor_name = payment.employee.get_full_name() or payment.employee.username
        self.vendor_email = payment.employee.email
        self.vendor_phone = payment.employee.phone_number
        
        self.remarks = payment.remarks
        self.reference_number = f"SAL-{payment.id}"
        
        # Recurring - Defaults
        self.is_recurring = False
        self.recurring_frequency = None
        
        # Payment info
        self.payment_method = payment.payment_method or 'bank_transfer'
        
        # Map status
        if payment.status in ['paid', 'early_paid']:
            self.payment_status = 'completed'
        else:
            self.payment_status = payment.status
            
        self.receipt = None
        self.created_by = payment.processed_by
        self.last_modified_by = payment.processed_by
        self.created_at = payment.created_at
        self.updated_at = payment.updated_at
        
        # Mock Category
        class CategoryMock:
            name = 'Employee Salaries'
            id = 0
            def __str__(self): return 'Employee Salaries'
        self.category = CategoryMock()

    def get_type_display(self):
        return 'Employee Salaries'
    
    def get_payment_status_display(self):
        return self._payment.get_status_display()
    
    def get_payment_method_display(self):
        return self._payment.get_payment_method_display() if self._payment.payment_method else 'Bank Transfer'
    
    @property
    def formatted_amount(self):
        return f"${self.amount:,.2f}"
        
    @property
    def pk(self):
        return self.id

class ExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View for retrieving, updating and deleting a specific expense record
    """
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_object(self):
        """
        Override to handle both Expense and SalaryPayment details
        """
        lookup_url_kwarg = self.lookup_field
        lookup = self.kwargs.get(lookup_url_kwarg)
        
        try:
            expense_id = int(lookup)
            # Check if this is a Salary Payment (ID > 2000000)
            if expense_id > 2000000:
                sp_id = expense_id - 2000000
                try:
                    salary_payment = SalaryPayment.objects.get(id=sp_id)
                    return SalaryPaymentWrapper(salary_payment)
                except SalaryPayment.DoesNotExist:
                    from django.http import Http404
                    raise Http404("Salary Payment not found")
        except (ValueError, TypeError):
            pass
            
        return super().get_object()

    def perform_update(self, serializer):
        """Set the last_modified_by user when updating expense"""
        if isinstance(serializer.instance, SalaryPaymentWrapper):
            # Block updates for Salary Payments via this endpoint
            return
            
        serializer.save(last_modified_by=self.request.user)

class IncomeCategoryListCreateView(generics.ListCreateAPIView):
    """
    View for listing and creating income categories
    """
    queryset = IncomeCategory.objects.filter(is_active=True)
    serializer_class = IncomeCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ['name', 'description']

class IncomeCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View for retrieving, updating and deleting a specific income category
    """
    queryset = IncomeCategory.objects.all()
    serializer_class = IncomeCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

class ExpenseCategoryListCreateView(generics.ListCreateAPIView):
    """
    View for listing and creating expense categories
    """
    queryset = ExpenseCategory.objects.filter(is_active=True)
    serializer_class = ExpenseCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ['name', 'description']

class ExpenseCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View for retrieving, updating and deleting a specific expense category
    """
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

class FinanceStatsView(generics.GenericAPIView):
    """
    View for getting financial statistics
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Date range filtering
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        income_queryset = Income.objects.all()
        expense_queryset = Expense.objects.all()
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                income_queryset = income_queryset.filter(date__gte=start_date)
                expense_queryset = expense_queryset.filter(date__gte=start_date)
            except ValueError:
                pass
                
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                income_queryset = income_queryset.filter(date__lte=end_date)
                expense_queryset = expense_queryset.filter(date__lte=end_date)
            except ValueError:
                pass
        
        # Basic statistics
        total_income_regular = income_queryset.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Calculate Client Payment totals
        cp_queryset = ClientPayment.objects.filter(status__in=['paid', 'early_paid', 'partial'])
        if start_date:
            try:
                sd = datetime.strptime(start_date, '%Y-%m-%d').date()
                cp_queryset = cp_queryset.filter(payment_date__date__gte=sd)
            except ValueError: pass
        if end_date:
            try:
                ed = datetime.strptime(end_date, '%Y-%m-%d').date()
                cp_queryset = cp_queryset.filter(payment_date__date__lte=ed)
            except ValueError: pass
            
        total_income_cp = cp_queryset.aggregate(total=Sum('net_amount'))['total'] or 0
        
        # Combine
        total_income = total_income_regular + total_income_cp
        
        total_expense_regular = expense_queryset.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Calculate Salary Payment totals
        sp_queryset = SalaryPayment.objects.filter(status__in=['paid', 'early_paid', 'overdue'])
        if start_date:
            try:
                sd = datetime.strptime(start_date, '%Y-%m-%d').date()
                sp_queryset = sp_queryset.filter(payment_date__date__gte=sd)
            except ValueError: pass
        if end_date:
            try:
                ed = datetime.strptime(end_date, '%Y-%m-%d').date()
                sp_queryset = sp_queryset.filter(payment_date__date__lte=ed)
            except ValueError: pass
            
        total_expense_sp = sp_queryset.aggregate(total=Sum('net_amount'))['total'] or 0
        
        # Combine
        total_expense = total_expense_regular + total_expense_sp
        
        net_balance = total_income - total_expense
        
        # Count statistics
        income_count = income_queryset.count()
        expense_count = expense_queryset.count()
        
        # Income statistics by type
        income_by_type = income_queryset.values('type').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        # Expense statistics by type
        expense_by_type = expense_queryset.values('type').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        # Income statistics by category
        income_by_category = income_queryset.values('category__name').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        # Expense statistics by category
        expense_by_category = expense_queryset.values('category__name').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        # Payment status statistics
        income_by_payment_status = income_queryset.values('payment_status').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        expense_by_payment_status = expense_queryset.values('payment_status').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        # Monthly trends (last 6 months)
        six_months_ago = timezone.now().date() - timedelta(days=180)
        
        monthly_income = income_queryset.filter(
            date__gte=six_months_ago
        ).extra(
            {'month': "EXTRACT(month FROM date)", 'year': "EXTRACT(year FROM date)"}
        ).values('year', 'month').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('year', 'month')
        
        monthly_expense = expense_queryset.filter(
            date__gte=six_months_ago
        ).extra(
            {'month': "EXTRACT(month FROM date)", 'year': "EXTRACT(year FROM date)"}
        ).values('year', 'month').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('year', 'month')
        
        # Top income sources
        top_income_sources = income_queryset.values('client_name').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')[:10]
        
        # Top expense vendors
        top_expense_vendors = expense_queryset.values('vendor_name').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')[:10]
        
        # Recurring transactions
        recurring_income = income_queryset.filter(is_recurring=True).count()
        recurring_expense = expense_queryset.filter(is_recurring=True).count()
        
        stats = {
            'total_income': float(total_income),
            'total_expense': float(total_expense),
            'net_balance': float(net_balance),
            'income_count': income_count,
            'expense_count': expense_count,
            'income_by_type': list(income_by_type),
            'expense_by_type': list(expense_by_type),
            'income_by_category': list(income_by_category),
            'expense_by_category': list(expense_by_category),
            'income_by_payment_status': list(income_by_payment_status),
            'expense_by_payment_status': list(expense_by_payment_status),
            'monthly_income_trend': list(monthly_income),
            'monthly_expense_trend': list(monthly_expense),
            'top_income_sources': list(top_income_sources),
            'top_expense_vendors': list(top_expense_vendors),
            'recurring_income_count': recurring_income,
            'recurring_expense_count': recurring_expense,
        }
        
        return Response(stats, status=status.HTTP_200_OK)

class RecentTransactionsView(generics.ListAPIView):
    """
    View for listing recent income and expense transactions
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        limit = int(request.query_params.get('limit', 10))
        
        recent_income = Income.objects.all().order_by('-date', '-created_at')[:limit]
        recent_expense = Expense.objects.all().order_by('-date', '-created_at')[:limit]
        
        income_serializer = IncomeListSerializer(recent_income, many=True)
        expense_serializer = ExpenseListSerializer(recent_expense, many=True)
        
        return Response({
            'recent_income': income_serializer.data,
            'recent_expense': expense_serializer.data
        }, status=status.HTTP_200_OK)

class UpcomingRecurringTransactionsView(generics.ListAPIView):
    """
    View for listing upcoming recurring transactions
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # This would typically integrate with a more sophisticated recurring system
        # For now, we'll return recurring transactions from the current month
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        recurring_income = Income.objects.filter(
            is_recurring=True,
            date__month=current_month,
            date__year=current_year
        )
        
        recurring_expense = Expense.objects.filter(
            is_recurring=True,
            date__month=current_month,
            date__year=current_year
        )
        
        income_serializer = IncomeListSerializer(recurring_income, many=True)
        expense_serializer = ExpenseListSerializer(recurring_expense, many=True)
        
        return Response({
            'recurring_income': income_serializer.data,
            'recurring_expense': expense_serializer.data
        }, status=status.HTTP_200_OK)

class FinancialSummaryView(generics.ListAPIView):
    """
    View for listing financial summaries
    """
    queryset = FinancialSummary.objects.all()
    serializer_class = FinancialSummarySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [OrderingFilter]
    ordering_fields = ['period_start', 'period_end']
    ordering = ['-period_start']

    def get_queryset(self):
        """
        Optionally filter by period type or date range
        """
        queryset = FinancialSummary.objects.all()
        
        period_type = self.request.query_params.get('period_type', None)
        if period_type:
            queryset = queryset.filter(period_type=period_type)
            
        return queryset

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_financial_summary(request):
    """
    Endpoint to generate financial summaries for a specific period
    """
    if request.method == 'POST':
        period_type = request.data.get('period_type', 'monthly')
        period_start = request.data.get('period_start')
        period_end = request.data.get('period_end')
        
        if not period_start or not period_end:
            return Response({
                'error': 'period_start and period_end are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            period_start = datetime.strptime(period_start, '%Y-%m-%d').date()
            period_end = datetime.strptime(period_end, '%Y-%m-%d').date()
        except ValueError:
            return Response({
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if summary already exists
        existing_summary = FinancialSummary.objects.filter(
            period_type=period_type,
            period_start=period_start,
            period_end=period_end
        ).first()
        
        if existing_summary:
            return Response({
                'message': 'Financial summary already exists for this period',
                'summary_id': existing_summary.id
            }, status=status.HTTP_200_OK)
        
        # Calculate totals for the period
        income_total_regular = Income.objects.filter(
            date__gte=period_start,
            date__lte=period_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        income_total_cp = ClientPayment.objects.filter(
            status__in=['paid', 'early_paid', 'partial'],
            payment_date__date__gte=period_start,
            payment_date__date__lte=period_end
        ).aggregate(total=Sum('net_amount'))['total'] or 0
        
        income_total = income_total_regular + income_total_cp
        
        expense_total_regular = Expense.objects.filter(
            date__gte=period_start,
            date__lte=period_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        expense_total_sp = SalaryPayment.objects.filter(
            status__in=['paid', 'early_paid', 'overdue'],
            payment_date__date__gte=period_start,
            payment_date__date__lte=period_end
        ).aggregate(total=Sum('net_amount'))['total'] or 0
        
        expense_total = expense_total_regular + expense_total_sp
        
        income_count_regular = Income.objects.filter(
            date__gte=period_start,
            date__lte=period_end
        ).count()
        
        income_count_cp = ClientPayment.objects.filter(
            status__in=['paid', 'early_paid', 'partial'],
            payment_date__date__gte=period_start,
            payment_date__date__lte=period_end
        ).count()
        
        income_count = income_count_regular + income_count_cp
        
        expense_count_regular = Expense.objects.filter(
            date__gte=period_start,
            date__lte=period_end
        ).count()
        
        expense_count_sp = SalaryPayment.objects.filter(
            status__in=['paid', 'early_paid', 'overdue'],
            payment_date__date__gte=period_start,
            payment_date__date__lte=period_end
        ).count()
        
        expense_count = expense_count_regular + expense_count_sp
        
        net_balance = income_total - expense_total
        
        # Create financial summary
        summary = FinancialSummary.objects.create(
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            total_income=income_total,
            total_expenses=expense_total,
            net_balance=net_balance,
            income_count=income_count,
            expense_count=expense_count
        )
        
        serializer = FinancialSummarySerializer(summary)
        
        return Response({
            'message': 'Financial summary generated successfully',
            'summary': serializer.data
        }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def export_financial_data(request):
    """
    Endpoint to export financial data in various formats
    """
    format_type = request.query_params.get('format', 'json')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    income_queryset = Income.objects.all()
    expense_queryset = Expense.objects.all()
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            income_queryset = income_queryset.filter(date__gte=start_date)
            expense_queryset = expense_queryset.filter(date__gte=start_date)
        except ValueError:
            pass
            
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            income_queryset = income_queryset.filter(date__lte=end_date)
            expense_queryset = expense_queryset.filter(date__lte=end_date)
        except ValueError:
            pass
    
    income_data = IncomeListSerializer(income_queryset, many=True).data
    expense_data = ExpenseListSerializer(expense_queryset, many=True).data
    
    if format_type == 'csv':
        # You would implement CSV export logic here
        return Response({
            'message': 'CSV export would be implemented here',
            'income_count': len(income_data),
            'expense_count': len(expense_data)
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'income': income_data,
            'expense': expense_data,
            'metadata': {
                'exported_at': timezone.now(),
                'income_count': len(income_data),
                'expense_count': len(expense_data),
                'date_range': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
        }, status=status.HTTP_200_OK)