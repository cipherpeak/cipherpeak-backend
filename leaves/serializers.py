from rest_framework import serializers
from emplyees.models import LeaveManagement
from datetime import datetime

class LeaveApplicationSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_details = serializers.SerializerMethodField()
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    monthly_leave_count = serializers.SerializerMethodField()
    leave_type = serializers.CharField(source='category', read_only=True)
    applied_date = serializers.DateTimeField(source='created_at', read_only=True)
    status = serializers.SerializerMethodField()
    address_during_leave = serializers.SerializerMethodField()
    

    class Meta:
        model = LeaveManagement
        fields = [
            'id', 'employee', 'employee_name', 'employee_details',
            'leave_type', 'start_date', 'end_date', 'total_days',
            'reason', 'status', 'applied_date',
            'approved_by', 'approved_by_name', 'monthly_leave_count',
            'attachment', 'remarks', 'approved_at',
            'address_during_leave', 
        ]

    def get_status(self, obj):
        if obj.status != 'approved':
            return obj.status
        
        try:
            today = datetime.now().date()
            start = datetime.strptime(obj.start_date, '%Y-%m-%d').date()
            end = datetime.strptime(obj.end_date, '%Y-%m-%d').date()
            
            if today > end:
                return 'approved' # Past
            if start <= today <= end:
                return 'active'
            if start > today:
                return 'upcoming'
        except:
            pass
        return obj.status

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
        try:
            # Handle string dates in LeaveManagement
            if isinstance(obj.start_date, str):
                date_obj = datetime.strptime(obj.start_date, '%Y-%m-%d')
                month = date_obj.month
                year = date_obj.year
            else:
                month = obj.start_date.month
                year = obj.start_date.year
            
            return LeaveManagement.objects.filter(
                employee=obj.employee,
                status='approved',
                start_date__icontains=f"{year}-{month:02d}"
            ).count()
        except:
            return 0

    def get_address_during_leave(self, obj):
        """Return the address during leave or 'Not Provided' if empty"""
        address = obj.address_during_leave
        # Check if address exists and is not just whitespace
        if address and str(address).strip():
            return str(address).strip()
        return 'Not Provided'


class LeaveProcessSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    remarks = serializers.CharField(required=False, allow_blank=True)
