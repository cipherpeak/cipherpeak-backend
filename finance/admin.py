from django.contrib import admin

# Register your models here.
# admin.py
from django.contrib import admin
from .models import IncomeCategory, ExpenseCategory, Income, Expense, FinancialSummary

@admin.register(IncomeCategory)
class IncomeCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ['type', 'amount', 'category', 'client_name', 'date', 'payment_status']
    list_filter = ['type', 'category', 'payment_status', 'date']
    search_fields = ['client_name', 'remarks', 'reference_number']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['type', 'amount', 'category', 'vendor_name', 'date', 'payment_status']
    list_filter = ['type', 'category', 'payment_status', 'date']
    search_fields = ['vendor_name', 'remarks', 'reference_number']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'

@admin.register(FinancialSummary)
class FinancialSummaryAdmin(admin.ModelAdmin):
    list_display = ['period_type', 'period_start', 'period_end', 'total_income', 'total_expenses', 'net_balance']
    list_filter = ['period_type']
    readonly_fields = ['created_at', 'updated_at']