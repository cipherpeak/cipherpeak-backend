from rest_framework import serializers
from .models import LeaveApplication
from django.utils import timezone

class LeaveApplicationSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_details = serializers.SerializerMethodField()
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    monthly_leave_count = serializers.SerializerMethodField()

    class Meta:
        model = LeaveApplication
        fields = [
            'id', 'employee', 'employee_name', 'employee_details',
            'leave_type', 'start_date', 'end_date', 'total_days',
            'reason', 'address_during_leave', 'passport_required_from',
            'passport_required_to', 'status', 'applied_date',
            'approved_by', 'approved_by_name', 'monthly_leave_count',
            'attachment', 'remarks', 'approved_at'
        ]

    def get_employee_details(self, obj):
        user = obj.employee
        return {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'employee_id': getattr(user, 'employee_id', f"EMP{user.id}"),
            'department': getattr(user, 'department', 'N/A'),
            'branch': getattr(user, 'branch', 'N/A'),
            'mobile': getattr(user, 'phone_number', 'N/A'),
            'email': user.email,
            'profile_picture': user.profile_image.url if getattr(user, 'profile_image', None) and hasattr(user.profile_image, 'url') else None,
            'designation': getattr(user, 'designation', 'N/A'),
        }

    def get_monthly_leave_count(self, obj):
        month = obj.start_date.month
        year = obj.start_date.year
        return LeaveApplication.objects.filter(
            employee=obj.employee,
            status='approved',
            start_date__month=month,
            start_date__year=year
        ).count()

class LeaveProcessSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    remarks = serializers.CharField(required=False, allow_blank=True)
