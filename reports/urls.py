from django.urls import path
from . import views

urlpatterns = [
    path('monthly/clients/', views.MonthlyClientReportView.as_view(), name='monthly-client-report'),
    path('monthly/employees/', views.MonthlyEmployeeReportView.as_view(), name='monthly-employee-report'),
    path('monthly/income/', views.MonthlyIncomeReportView.as_view(), name='monthly-income-report'),
    path('monthly/expense/', views.MonthlyExpenseReportView.as_view(), name='monthly-expense-report'),
]
