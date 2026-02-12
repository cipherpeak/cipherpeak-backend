from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from django.utils import timezone
from .utils import (
    get_monthly_client_data, 
    get_monthly_employee_data,
    get_detailed_finance_data
)
from .models import MonthlyEmployeeReport,MonthlyClientReport, MonthlyIncomeReport,MonthlyExpenseReport
from .serializers import (
    MonthlyEmployeeReportSerializer,
    MonthlyClientReportSerializer,
    MonthlyIncomeReportSerializer,
    MonthlyExpenseReportSerializer
)

class BaseReportView(APIView):
    """
    Base view to handle common month/year parsing for reports.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_month_year(self, request):
        now = timezone.now()
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        
        try:
            month = int(month) if month else now.month
            year = int(year) if year else now.year
            return month, year
        except ValueError:
            return None, None

class MonthlyClientReportView(BaseReportView):
    """
    API view for client-specific revenue and tasks.
    """
    def get(self, request, *args, **kwargs):
        month, year = self.get_month_year(request)
        if not month:
            return Response({'error': 'Invalid month or year'}, status=status.HTTP_400_BAD_REQUEST)

        data = get_monthly_client_data(month, year)
        
        # Persistence: Save Snapshot
        summary = data['summary']
        MonthlyClientReport.objects.update_or_create(
            month=month,
            year=year,
            defaults={
                'total_revenue': summary['total_revenue'],
                'total_tax': summary['total_tax'],
                'total_discount': summary['total_discount'],
                'expected_revenue': summary['total_expected_revenue'],
                'client_count': summary['count'],
                'generated_by': request.user
            }
        )
        
        # Remove Company-wide summary and tasks before returning
        if 'summary' in data:
            del data['summary']
        if 'tasks' in data:
            del data['tasks']
            
        return Response(data)

class MonthlyEmployeeReportView(BaseReportView):
    """
    API view for employee payroll and tasks.
    """
    def get(self, request, *args, **kwargs):
        month, year = self.get_month_year(request)
        if not month:
            return Response({'error': 'Invalid month or year'}, status=status.HTTP_400_BAD_REQUEST)

        data = get_monthly_employee_data(month, year)
        
        # Persistence: Save Snapshot
        summary = data['summary']
        MonthlyEmployeeReport.objects.update_or_create(
            month=month,
            year=year,
            defaults={
                'total_base_salary': summary['total_base_salary'],
                'total_incentives': summary['total_incentives'],
                'total_deductions': summary['total_deductions'],
                'total_net_paid': summary['total_net_paid'],
                'total_leave_days': summary['total_leave_days'],
                'expected_salary': summary['total_expected_salary'],
                'employee_count': summary['count'],
                'generated_by': request.user
            }
        )
        
        # Remove Company-wide summary before returning
        if 'summary' in data:
            del data['summary']
            
        return Response(data)

class MonthlyIncomeReportView(BaseReportView):
    """
    API view for detailed monthly income.
    """
    def get(self, request, *args, **kwargs):
        month, year = self.get_month_year(request)
        if not month:
            return Response({'error': 'Invalid month or year'}, status=status.HTTP_400_BAD_REQUEST)

        data = get_detailed_finance_data(month, year)

        # Persistence: Save Snapshot
        MonthlyIncomeReport.objects.update_or_create(
            month=month,
            year=year,
            defaults={
                'total_income': data['income']['total'],
                'income_count': data['income']['count'],
                'generated_by': request.user
            }
        )

        return Response({
            'month': data['month'],
            'month_name': data['month_name'],
            'year': data['year'],
            'income': data['income']
        })

class MonthlyExpenseReportView(BaseReportView):
    """
    API view for detailed monthly expenses.
    """
    def get(self, request, *args, **kwargs):
        month, year = self.get_month_year(request)
        if not month:
            return Response({'error': 'Invalid month or year'}, status=status.HTTP_400_BAD_REQUEST)

        data = get_detailed_finance_data(month, year)

        # Persistence: Save Snapshot
        MonthlyExpenseReport.objects.update_or_create(
            month=month,
            year=year,
            defaults={
                'total_expense': data['expense']['total'],
                'expense_count': data['expense']['count'],
                'generated_by': request.user
            }
        )

        return Response({
            'month': data['month'],
            'month_name': data['month_name'],
            'year': data['year'],
            'expense': data['expense']
        })
