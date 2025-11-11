# finance/serializers.py
from rest_framework import serializers
from .models import Income, Expense, IncomeCategory, ExpenseCategory, FinancialSummary

class IncomeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeCategory
        fields = ['id', 'name', 'description', 'is_active']

class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ['id', 'name', 'description', 'is_active']

class IncomeListSerializer(serializers.ModelSerializer):
    """Serializer for listing incomes (read-only fields for display)"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    formatted_amount = serializers.CharField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Income
        fields = [
            'id', 'type', 'type_display', 'amount', 'formatted_amount', 
            'category', 'category_name', 'date', 'client_name', 
            'remarks', 'reference_number', 'is_recurring', 'recurring_frequency',
            'payment_method', 'payment_method_display', 'payment_status', 
            'payment_status_display', 'created_by', 'created_by_name',
            'last_modified_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'last_modified_by', 'created_at', 'updated_at']

class IncomeSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating incomes"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    formatted_amount = serializers.CharField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Income
        fields = [
            'id', 'type', 'type_display', 'amount', 'formatted_amount', 
            'category', 'category_name', 'date', 'client_name', 'client_email',
            'client_phone', 'remarks', 'reference_number', 'is_recurring', 
            'recurring_frequency', 'payment_method', 'payment_method_display', 
            'payment_status', 'payment_status_display', 'attachment', 
            'created_by', 'created_by_name', 'last_modified_by', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'last_modified_by', 'created_at', 'updated_at']

class ExpenseListSerializer(serializers.ModelSerializer):
    """Serializer for listing expenses (read-only fields for display)"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    formatted_amount = serializers.CharField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Expense
        fields = [
            'id', 'type', 'type_display', 'amount', 'formatted_amount', 
            'category', 'category_name', 'date', 'vendor_name', 
            'remarks', 'reference_number', 'is_recurring', 'recurring_frequency',
            'payment_method', 'payment_method_display', 'payment_status', 
            'payment_status_display', 'created_by', 'created_by_name',
            'last_modified_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'last_modified_by', 'created_at', 'updated_at']

class ExpenseSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating expenses"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    formatted_amount = serializers.CharField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Expense
        fields = [
            'id', 'type', 'type_display', 'amount', 'formatted_amount', 
            'category', 'category_name', 'date', 'vendor_name', 'vendor_contact',
            'vendor_email', 'vendor_phone', 'remarks', 'reference_number', 
            'is_recurring', 'recurring_frequency', 'payment_method', 
            'payment_method_display', 'payment_status', 'payment_status_display', 
            'receipt', 'created_by', 'created_by_name', 'last_modified_by', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'last_modified_by', 'created_at', 'updated_at']

class FinancialSummarySerializer(serializers.ModelSerializer):
    """Serializer for financial summaries"""
    period_display = serializers.CharField(source='get_period_type_display', read_only=True)
    
    class Meta:
        model = FinancialSummary
        fields = [
            'id', 'period_type', 'period_display', 'period_start', 'period_end',
            'total_income', 'total_expenses', 'net_balance', 'income_count',
            'expense_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

# Additional serializers for specific operations
class IncomePaymentStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating income payment status"""
    class Meta:
        model = Income
        fields = ['payment_status', 'payment_method']
    
    def update(self, instance, validated_data):
        instance.payment_status = validated_data.get('payment_status', instance.payment_status)
        instance.payment_method = validated_data.get('payment_method', instance.payment_method)
        instance.save()
        return instance

class ExpensePaymentStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating expense payment status"""
    class Meta:
        model = Expense
        fields = ['payment_status', 'payment_method']
    
    def update(self, instance, validated_data):
        instance.payment_status = validated_data.get('payment_status', instance.payment_status)
        instance.payment_method = validated_data.get('payment_method', instance.payment_method)
        instance.save()
        return instance

class IncomeRecurringUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating income recurring settings"""
    class Meta:
        model = Income
        fields = ['is_recurring', 'recurring_frequency']
    
    def validate(self, data):
        is_recurring = data.get('is_recurring', False)
        recurring_frequency = data.get('recurring_frequency')
        
        if is_recurring and not recurring_frequency:
            raise serializers.ValidationError({
                'recurring_frequency': 'Recurring frequency is required when is_recurring is True'
            })
        
        return data

class ExpenseRecurringUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating expense recurring settings"""
    class Meta:
        model = Expense
        fields = ['is_recurring', 'recurring_frequency']
    
    def validate(self, data):
        is_recurring = data.get('is_recurring', False)
        recurring_frequency = data.get('recurring_frequency')
        
        if is_recurring and not recurring_frequency:
            raise serializers.ValidationError({
                'recurring_frequency': 'Recurring frequency is required when is_recurring is True'
            })
        
        return data

# Statistics serializers
class IncomeStatsSerializer(serializers.Serializer):
    """Serializer for income statistics"""
    total_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    income_count = serializers.IntegerField()
    avg_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    max_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    min_income = serializers.DecimalField(max_digits=12, decimal_places=2)

class ExpenseStatsSerializer(serializers.Serializer):
    """Serializer for expense statistics"""
    total_expense = serializers.DecimalField(max_digits=12, decimal_places=2)
    expense_count = serializers.IntegerField()
    avg_expense = serializers.DecimalField(max_digits=12, decimal_places=2)
    max_expense = serializers.DecimalField(max_digits=12, decimal_places=2)
    min_expense = serializers.DecimalField(max_digits=12, decimal_places=2)

class FinanceStatsSerializer(serializers.Serializer):
    """Serializer for overall finance statistics"""
    total_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_expense = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    income_count = serializers.IntegerField()
    expense_count = serializers.IntegerField()
    
    # Income statistics by type
    income_by_type = serializers.ListField(child=serializers.DictField())
    
    # Expense statistics by type
    expense_by_type = serializers.ListField(child=serializers.DictField())
    
    # Income statistics by category
    income_by_category = serializers.ListField(child=serializers.DictField())
    
    # Expense statistics by category
    expense_by_category = serializers.ListField(child=serializers.DictField())
    
    # Payment status statistics
    income_by_payment_status = serializers.ListField(child=serializers.DictField())
    expense_by_payment_status = serializers.ListField(child=serializers.DictField())
    
    # Monthly trends
    monthly_income_trend = serializers.ListField(child=serializers.DictField())
    monthly_expense_trend = serializers.ListField(child=serializers.DictField())
    
    # Top sources/vendors
    top_income_sources = serializers.ListField(child=serializers.DictField())
    top_expense_vendors = serializers.ListField(child=serializers.DictField())
    
    # Recurring transactions
    recurring_income_count = serializers.IntegerField()
    recurring_expense_count = serializers.IntegerField()

# Bulk operation serializers
class BulkIncomeCreateSerializer(serializers.ListSerializer):
    """Serializer for bulk income creation"""
    child = IncomeSerializer()
    
    def create(self, validated_data):
        incomes = [Income(**item) for item in validated_data]
        return Income.objects.bulk_create(incomes)

class BulkExpenseCreateSerializer(serializers.ListSerializer):
    """Serializer for bulk expense creation"""
    child = ExpenseSerializer()
    
    def create(self, validated_data):
        expenses = [Expense(**item) for item in validated_data]
        return Expense.objects.bulk_create(expenses)

# Import/Export serializers
class IncomeImportSerializer(serializers.ModelSerializer):
    """Serializer for income data import"""
    class Meta:
        model = Income
        fields = [
            'type', 'amount', 'category', 'date', 'client_name', 
            'remarks', 'payment_method', 'payment_status'
        ]
    
    def validate_category(self, value):
        """Ensure category exists or create it"""
        if isinstance(value, str):
            category, created = IncomeCategory.objects.get_or_create(
                name=value,
                defaults={'description': f'Automatically created category: {value}'}
            )
            return category.id
        return value

class ExpenseImportSerializer(serializers.ModelSerializer):
    """Serializer for expense data import"""
    class Meta:
        model = Expense
        fields = [
            'type', 'amount', 'category', 'date', 'vendor_name', 
            'remarks', 'payment_method', 'payment_status'
        ]
    
    def validate_category(self, value):
        """Ensure category exists or create it"""
        if isinstance(value, str):
            category, created = ExpenseCategory.objects.get_or_create(
                name=value,
                defaults={'description': f'Automatically created category: {value}'}
            )
            return category.id
        return value