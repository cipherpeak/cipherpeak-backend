from rest_framework import serializers
from .models import CustomUser, EmployeeDocument, EmployeeMedia, LeaveManagement, SalaryPayment, CameraDepartment,LeaveBalance
from django.contrib.auth import authenticate



#login serializer
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        login_value = data.get('username')
        password = data.get('password')
        
        if login_value and password:
            # Try to authenticate with username
            user = authenticate(username=login_value, password=password)
            
            # If username authentication fails, try with email
            if not user:
                try:
                    user_obj = CustomUser.objects.get(email=login_value)
                    user = authenticate(username=user_obj.username, password=password)
                except CustomUser.DoesNotExist:
                    user = None

            if user:
                if user.is_active:
                    data['user'] = user
                else:
                    raise serializers.ValidationError('User account is disabled.')
            else:
                raise serializers.ValidationError('Unable to log in with provided credentials.')
        else:
            raise serializers.ValidationError('Must include login (username or email) and password.')
        return data


#employee list serializer
class EmployeeListSerializer(serializers.ModelSerializer):
    profile_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'role', 'current_status', 'department',
            'designation','profile_image_url', 'date_of_birth',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_profile_image_url(self, obj):
        if obj.profile_image and hasattr(obj.profile_image, 'url'):
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.profile_image.url)
            return obj.profile_image.url
        return None


#employee create serializer
class EmployeeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'date_of_birth',
            'gender',
            'address',
            'city',
            'state',
            'postal_code',
            'country',
            'emergency_contact_name',
            'emergency_contact_phone',
            'emergency_contact_relation',
            'employee_id',
            'role',
            'department',
            'designation',
            'salary',
            'current_status',
            'joining_date',
            'profile_image',  
            'password',
        ]

        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'role': {'required': True},
            'current_status': {'required': True},
            'joining_date': {'required': True},
            'profile_image': {'required': False},
            'password': {'write_only': True, 'required': True},
        }

    def validate_username(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long.")
        return value

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email is required.")
        return value

    def validate_salary(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Salary cannot be negative.")
        return value

    def validate_joining_date(self, value):
        from django.utils import timezone
        if value and value > timezone.now().date():
            raise serializers.ValidationError("Joining date cannot be in the future.")
        return value

    def validate_profile_image(self, value):
        
        if value:
            max_size = 5 * 1024 * 1024  
            if value.size > max_size:
                raise serializers.ValidationError("Profile image size cannot exceed 5MB.")
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp']
            extension = value.name.split('.')[-1].lower()
            if extension not in valid_extensions:
                raise serializers.ValidationError(
                    f"Unsupported file format. Supported formats: {', '.join(valid_extensions)}"
                )
        return value


#employee update serializer
class EmployeeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'date_of_birth',
            'gender',
            'address',
            'city',
            'state',
            'postal_code',
            'country',
            'emergency_contact_name',
            'emergency_contact_phone',
            'emergency_contact_relation',
            'employee_id',
            'role',
            'department',
            'designation',
            'salary',
            'current_status',
            'joining_date',
            'profile_image',
        ]
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'role': {'required': False},
            'current_status': {'required': False},
            'joining_date': {'required': False},
            'profile_image': {'required': False},
        }

    def validate_username(self, value):
        if value and len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long.")
        return value

    def validate_salary(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Salary cannot be negative.")
        return value

    def validate_joining_date(self, value):
        from django.utils import timezone
        if value and value > timezone.now().date():
            raise serializers.ValidationError("Joining date cannot be in the future.")
        return value

    def validate_profile_image(self, value):
        if value:
            max_size = 5 * 1024 * 1024  
            if value.size > max_size:
                raise serializers.ValidationError("Profile image size cannot exceed 5MB.")
            
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp']
            extension = value.name.split('.')[-1].lower()
            if extension not in valid_extensions:
                raise serializers.ValidationError(
                    f"Unsupported file format. Supported formats: {', '.join(valid_extensions)}"
                )
        return value


#employee document serializer (for reading)
class EmployeeDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = EmployeeDocument
        fields = [
            'id', 'document_type', 'file_url', 'uploaded_at'
        ]
        
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


#employee document create serializer (for uploading)
class EmployeeDocumentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDocument
        fields = ['document_type', 'file']
        
    def validate_file(self, value):
        if value:
            max_size = 10 * 1024 * 1024  # 10MB
            if value.size > max_size:
                raise serializers.ValidationError("Document size cannot exceed 10MB.")
        return value


#employee media serializer (for reading)
class EmployeeMediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = EmployeeMedia
        fields = [
            'id', 'media_type', 'file_url', 'uploaded_at'
        ]
       
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


#employee media create serializer (for uploading)
class EmployeeMediaCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeMedia
        fields = ['media_type', 'file']
        
    def validate_file(self, value):
        if value:
            max_size = 10 * 1024 * 1024  # 10MB
            if value.size > max_size:
                raise serializers.ValidationError("Media file size cannot exceed 10MB.")
        return value

#Leave list serializer
class LeaveListSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    approved_by_name = serializers.SerializerMethodField()
    applied_date = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = LeaveManagement
        fields = [
            'id', 'employee_name', 'employee_id', 'category', 'start_date', 'end_date',
            'total_days', 'reason', 'status', 'created_at', 'applied_date',
            'approved_by_name', 'approved_at', 'remarks', 'attachment'
        ]

    def get_employee_name(self, obj):
        name = obj.employee.get_full_name()
        return name if name.strip() else obj.employee.username

    def get_approved_by_name(self, obj):
        if not obj.approved_by:
            return None
        name = obj.approved_by.get_full_name()
        return name if name.strip() else obj.approved_by.username


# SalaryPayment serializer
class SalaryPaymentSerializer(serializers.ModelSerializer):
    processed_by_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SalaryPayment
        fields = [
            'id', 'employee', 'month', 'year',
            'base_salary', 'incentives', 'deductions', 'net_amount',
            'scheduled_date', 'payment_date', 'status', 'status_display',
            'payment_method', 'processed_by', 'processed_by_name', 'remarks'
        ]
        read_only_fields = ['created_at', 'net_amount']

    def get_processed_by_name(self, obj):
        if not obj.processed_by:
            return None
        name = obj.processed_by.get_full_name()
        return name if name.strip() else obj.processed_by.username





#employee detail serializer
class EmployeeDetailSerializer(serializers.ModelSerializer):
    documents = EmployeeDocumentSerializer(many=True, read_only=True)
    media_files = EmployeeMediaSerializer(many=True, read_only=True)
    leave_records = LeaveListSerializer(source='leaves', many=True, read_only=True)
    salary_payment_history = SalaryPaymentSerializer(source='salary_payments', many=True, read_only=True)
    full_name = serializers.SerializerMethodField()
    profile_image_url = serializers.SerializerMethodField()  
    payment_status = serializers.SerializerMethodField()
    payment_history_summary = serializers.SerializerMethodField()
    salary = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    class Meta:
        model = CustomUser
        fields = [
            'id','email','username','first_name', 'last_name', 'full_name',
            'phone_number', 'role', 'salary', 'payment_status', 'payment_history_summary', 'current_status', 'joining_date',
            'employee_id', 'department', 'designation', 'profile_image', 
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation',
            'address', 'city', 'state', 'postal_code', 'country',
            'date_of_birth', 'gender', 'profile_image_url',  
            'documents', 'media_files', 'leave_records', 'salary_payment_history',
        ]

    def get_full_name(self, obj):
        name = obj.get_full_name()
        return name if name.strip() else obj.username
    def _calculate_month_status(self, obj, m, y):
        from .models import SalaryPayment
        import calendar
        from datetime import date
        from django.utils import timezone
        
        payment = SalaryPayment.objects.filter(
            employee=obj,
            month=m,
            year=y
        ).first()
        
        if payment:
            return payment.status
            
        today = timezone.now().date()
        joining_month_start = date(obj.joining_date.year, obj.joining_date.month, 1)
        target_month_start = date(y, m, 1)
        
        if target_month_start < joining_month_start:
            return "not_joined"
            
        if (y > today.year) or (y == today.year and m > today.month):
            return "pending" # Future month

        _, last_day = calendar.monthrange(y, m)
        scheduled_date = date(y, m, last_day)
        
        if today > scheduled_date:
            return "overdue"
        elif today == scheduled_date:
            return "pay_now"
        elif (scheduled_date - today).days <= 7:
            return "coming_soon"
        else:
            return "pending"

    def get_payment_status(self, obj):
        from django.utils import timezone
        from datetime import date
        
        if not obj.joining_date:
            return "Unknown"

        today = timezone.now().date()
        curr_iter = date(obj.joining_date.year, obj.joining_date.month, 1)
        end_date = date(today.year, today.month, 1)
        
        while curr_iter <= end_date:
            m = curr_iter.month
            y = curr_iter.year
            
            status = self._calculate_month_status(obj, m, y)
            if status not in ['paid', 'early_paid']:
                if status == 'overdue':
                    return "Overdue"
                elif status == 'pay_now':
                    return "Pay Salary"
                elif status == 'coming_soon':
                    return "Payment date coming soon"
                else:
                    return "Pending"
            
            if curr_iter.month == 12:
                curr_iter = date(curr_iter.year + 1, 1, 1)
            else:
                curr_iter = date(curr_iter.year, curr_iter.month + 1, 1)

        # Check for early paid in future
        next_month = (today.month % 12) + 1
        next_year = today.year + (1 if today.month == 12 else 0)
        if self._calculate_month_status(obj, next_month, next_year) == 'early_paid':
            return "Early Salary Paid"
            
        return "Salary Paid"

    def get_payment_history_summary(self, obj):
        if not obj.joining_date:
            return []

        from django.utils import timezone
        from datetime import date
        
        today = timezone.now().date()
        current_year = today.year
        current_month = today.month
        
        next_month = (current_month % 12) + 1
        next_year = current_year + (1 if current_month == 12 else 0)
        
        summary = []
        curr_iter = date(obj.joining_date.year, obj.joining_date.month, 1)
        end_iter = date(next_year, next_month, 1)
        
        while curr_iter <= end_iter:
            m = curr_iter.month
            y = curr_iter.year
            
            status = self._calculate_month_status(obj, m, y)
            summary.append({
                'month': m,
                'year': y,
                'status': status,
                'status_display': status.replace('_', ' ').title()
            })
            
            if curr_iter.month == 12:
                curr_iter = date(curr_iter.year + 1, 1, 1)
            else:
                curr_iter = date(curr_iter.year, curr_iter.month + 1, 1)
                
        return summary

       

    
    def get_profile_image_url(self, obj):
        if obj.profile_image and hasattr(obj.profile_image, 'url'):
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.profile_image.url)
            return obj.profile_image.url
        return None


# camera department list serializer
class CameraDepartmentListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.client_name', read_only=True)
    employee_name = serializers.SerializerMethodField()
    class Meta:
        model = CameraDepartment
        fields = [
            'id', 'client', 'client_name', 'uploaded_date', 'priority','link','employee_name'
        ]

    def get_employee_name(self, obj):
        if not obj.employee:
            return None
        name = obj.employee.get_full_name()
        return name if name.strip() else obj.employee.username


#camera department create serializer
class CameraDepartmentCreateSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.client_name', read_only=True)
    
    class Meta:
        model = CameraDepartment
        fields = [
            'client', 'client_name', 'uploaded_date', 'priority', 'link'
        ]
        

#camera department detail serializer
class CameraDepartmentDetailSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.client_name', read_only=True)
    employee_name = serializers.SerializerMethodField()
    class Meta:
        model = CameraDepartment
        fields = [
            'id', 'client', 'client_name',  
            'uploaded_date', 'priority', 'link','employee_name'
        ]

    def get_employee_name(self, obj):
        if not obj.employee:
            return None
        name = obj.employee.get_full_name()
        return name if name.strip() else obj.employee.username


#Leave create serializer
class LeaveCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = LeaveManagement
        fields = [
            'category',
            'start_date',
            'end_date',
            'total_days',
            'reason',
           
            'attachment',
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['employee'] = request.user
        return super().create(validated_data)


#Leave detail serializer
class LeaveDetailSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = LeaveManagement
        fields = '__all__'

    def get_employee_name(self, obj):
        name = obj.employee.get_full_name()
        return name if name.strip() else obj.employee.username

    def get_approved_by_name(self, obj):
        if not obj.approved_by:
            return None
        name = obj.approved_by.get_full_name()
        return name if name.strip() else obj.approved_by.username


#leave update serializer
class LeaveUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveManagement
        fields = [
            'category', 
            'start_date', 
            'end_date', 
            'total_days', 
            'reason', 
            
            'attachment',
            'status', 
            'remarks',
        ]
        read_only_fields = ['employee', 'created_at', 'updated_at']

    def validate(self, data):
        return data


#payment detail serializer
class PaymentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryPayment
        fields = '__all__'


class LeaveApprovalRejectSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveManagement
        fields = [
            'status',
            'remarks',
            
            
        ]


class LeaveBalanceSerializer(serializers.ModelSerializer):
    annual_used = serializers.SerializerMethodField()
    casual_used = serializers.SerializerMethodField()
    sick_used = serializers.SerializerMethodField()
    
    annual_remaining = serializers.SerializerMethodField()
    casual_remaining = serializers.SerializerMethodField()
    sick_remaining = serializers.SerializerMethodField()
    
    total_balance = serializers.SerializerMethodField()
    leaves_used = serializers.SerializerMethodField()
    pending_requests = serializers.SerializerMethodField()
    upcoming_leaves = serializers.SerializerMethodField()

    class Meta:
        model = LeaveBalance
        fields = [
            'annual_total', 'casual_total', 'sick_total', 'year',
            'annual_used', 'casual_used', 'sick_used',
            'annual_remaining', 'casual_remaining', 'sick_remaining',
            'total_balance', 'leaves_used', 'pending_requests', 'upcoming_leaves'
        ]

    def get_used_days(self, obj, category):
        from django.db.models import Sum
        from .models import LeaveManagement
        
        year = obj.year
        used = LeaveManagement.objects.filter(
            employee=obj.employee,
            category=category,
            status='approved',
            created_at__year=year
        ).aggregate(Sum('total_days'))['total_days__sum'] or 0
        return float(used)

    def get_annual_used(self, obj):
        return self.get_used_days(obj, 'Annual Leave')

    def get_casual_used(self, obj):
        return self.get_used_days(obj, 'Casual Leave')

    def get_sick_used(self, obj):
        return self.get_used_days(obj, 'Sick Leave')

    def get_annual_remaining(self, obj):
        return float(obj.annual_total) - self.get_annual_used(obj)

    def get_casual_remaining(self, obj):
        return float(obj.casual_total) - self.get_casual_used(obj)

    def get_sick_remaining(self, obj):
        return float(obj.sick_total) - self.get_sick_used(obj)

    def get_total_balance(self, obj):
        return self.get_annual_remaining(obj) + self.get_casual_remaining(obj) + self.get_sick_remaining(obj)

    def get_leaves_used(self, obj):
        return self.get_annual_used(obj) + self.get_casual_used(obj) + self.get_sick_used(obj)

    def get_pending_requests(self, obj):
        from .models import LeaveManagement
        return LeaveManagement.objects.filter(
            employee=obj.employee,
            status='pending',
            created_at__year=obj.year
        ).count()

    def get_upcoming_leaves(self, obj):
        from .models import LeaveManagement
        return LeaveManagement.objects.filter(
            employee=obj.employee,
            status='approved',
            created_at__year=obj.year
        ).count()