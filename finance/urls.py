# finance/urls.py
from django.urls import path, include
from . import views


urlpatterns = [
    # Income URLs
    path('incomes/', views.IncomeListCreateView.as_view(), name='income-list-create'),
    path('incomes/<int:id>/', views.IncomeDetailView.as_view(), name='income-detail'),
    
    # Expense URLs
    path('expenses/', views.ExpenseListCreateView.as_view(), name='expense-list-create'),
    path('expenses/<int:id>/', views.ExpenseDetailView.as_view(), name='expense-detail'),
    
    # Category URLs
    path('income-categories/', views.IncomeCategoryListCreateView.as_view(), name='income-category-list'),
    path('income-categories/<int:id>/', views.IncomeCategoryDetailView.as_view(), name='income-category-detail'),
    path('expense-categories/', views.ExpenseCategoryListCreateView.as_view(), name='expense-category-list'),
    path('expense-categories/<int:id>/', views.ExpenseCategoryDetailView.as_view(), name='expense-category-detail'),
    
    # Statistics and Reports
    path('stats/', views.FinanceStatsView.as_view(), name='finance-stats'),
    path('recent-transactions/', views.RecentTransactionsView.as_view(), name='recent-transactions'),
    path('upcoming-recurring/', views.UpcomingRecurringTransactionsView.as_view(), name='upcoming-recurring'),
    path('financial-summaries/', views.FinancialSummaryView.as_view(), name='financial-summaries'),
    path('generate-summary/', views.generate_financial_summary, name='generate-summary'),
    path('export-data/', views.export_financial_data, name='export-data'),
]