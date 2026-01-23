from rest_framework import serializers
from .models import MonthlyEmployeeReport, MonthlyClientReport, MonthlyIncomeReport, MonthlyExpenseReport

class MonthlyEmployeeReportSerializer(serializers.ModelSerializer):
    month_name = serializers.SerializerMethodField()
    generated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = MonthlyEmployeeReport
        fields = [
            'id', 'month', 'month_name', 'year', 'total_base_salary', 
            'total_incentives', 'total_deductions', 'total_net_paid', 
            'total_leave_days', 'employee_count', 'generated_at', 'generated_by_name'
        ]

    def get_month_name(self, obj):
        import calendar
        return calendar.month_name[obj.month]

    def get_generated_by_name(self, obj):
        if obj.generated_by:
            return obj.generated_by.get_full_name() or obj.generated_by.username
        return "System"

class MonthlyClientReportSerializer(serializers.ModelSerializer):
    month_name = serializers.SerializerMethodField()
    generated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = MonthlyClientReport
        fields = [
            'id', 'month', 'month_name', 'year', 'total_revenue', 
            'total_tax', 'total_discount', 'client_count', 'generated_at', 'generated_by_name'
        ]

    def get_month_name(self, obj):
        import calendar
        return calendar.month_name[obj.month]

    def get_generated_by_name(self, obj):
        if obj.generated_by:
            return obj.generated_by.get_full_name() or obj.generated_by.username
        return "System"

class MonthlyIncomeReportSerializer(serializers.ModelSerializer):
    month_name = serializers.SerializerMethodField()
    generated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = MonthlyIncomeReport
        fields = [
            'id', 'month', 'month_name', 'year', 'total_income', 
            'income_count', 'generated_at', 'generated_by_name'
        ]

    def get_month_name(self, obj):
        import calendar
        return calendar.month_name[obj.month]

    def get_generated_by_name(self, obj):
        if obj.generated_by:
            return obj.generated_by.get_full_name() or obj.generated_by.username
        return "System"

class MonthlyExpenseReportSerializer(serializers.ModelSerializer):
    month_name = serializers.SerializerMethodField()
    generated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = MonthlyExpenseReport
        fields = [
            'id', 'month', 'month_name', 'year', 'total_expense', 
            'expense_count', 'generated_at', 'generated_by_name'
        ]

    def get_month_name(self, obj):
        import calendar
        return calendar.month_name[obj.month]

    def get_generated_by_name(self, obj):
        if obj.generated_by:
            return obj.generated_by.get_full_name() or obj.generated_by.username
        return "System"

class TaskReportDetailSerializer(serializers.Serializer):
    title = serializers.CharField()
    assignee = serializers.CharField()
    client = serializers.CharField()
    status = serializers.CharField()
    due_date = serializers.DateField()

class ClientReportDetailSerializer(serializers.Serializer):
    client_name = serializers.CharField()
    monthly_retainer = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    payment_cycle = serializers.CharField()
    tax_id = serializers.CharField(allow_blank=True, allow_null=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    tax = serializers.DecimalField(max_digits=12, decimal_places=2)
    discount = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_date = serializers.DateField(allow_null=True)
    payment_method = serializers.CharField(allow_blank=True, allow_null=True)
    transaction_id = serializers.CharField(allow_blank=True, allow_null=True)
    status = serializers.CharField()
    remarks = serializers.CharField(allow_blank=True, allow_null=True)
    
    # Content Verification Fields
    videos_target = serializers.IntegerField(default=0)
    videos_actual = serializers.IntegerField(default=0)
    posters_target = serializers.IntegerField(default=0)
    posters_actual = serializers.IntegerField(default=0)
    reels_target = serializers.IntegerField(default=0)
    reels_actual = serializers.IntegerField(default=0)
    stories_target = serializers.IntegerField(default=0)
    stories_actual = serializers.IntegerField(default=0)

class EmployeeReportDetailSerializer(serializers.Serializer):
    employee_name = serializers.CharField()
    department = serializers.CharField()
    base_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    incentives = serializers.DecimalField(max_digits=12, decimal_places=2)
    deductions = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_date = serializers.DateField(allow_null=True)
    status = serializers.CharField()
    leaves_count = serializers.DecimalField(max_digits=5, decimal_places=2)

class LeaveReportDetailSerializer(serializers.Serializer):
    employee_name = serializers.CharField()
    category = serializers.CharField()
    start_date = serializers.CharField()
    end_date = serializers.CharField()
    total_days = serializers.DecimalField(max_digits=5, decimal_places=2)
    status = serializers.CharField()
    reason = serializers.CharField(allow_blank=True, allow_null=True)

class GeneralTransactionDetailSerializer(serializers.Serializer):
    type = serializers.CharField()
    category = serializers.CharField()
    vendor_name = serializers.CharField(required=False, allow_null=True)
    client_name = serializers.CharField(required=False, allow_null=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    gst_amount = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    date = serializers.DateField()
    remarks = serializers.CharField(allow_blank=True, allow_null=True)
    payment_method = serializers.CharField(allow_blank=True, allow_null=True)
    status = serializers.CharField()
