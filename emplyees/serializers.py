from rest_framework import serializers
from .models import CustomUser, EmployeeDocument, EmployeeMedia, LeaveManagement, SalaryPayment, CameraDepartment, AdminNote,LeaveBalance
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
    employee_name = serializers.CharField(
        source='employee.get_full_name', read_only=True
    )
    employee_id = serializers.IntegerField(source='employee.id', read_only=True)
    approved_by_name = serializers.CharField(
        source='approved_by.get_full_name', read_only=True
    )

    class Meta:
        model = LeaveManagement
        fields = [
            'id', 'employee_name', 'employee_id', 'category', 'start_date', 'end_date',
            'total_days', 'reason', 'status', 'created_at',
            'approved_by_name', 'approved_at', 'remarks', 'attachment'
        ]


# SalaryPayment serializer
class SalaryPaymentSerializer(serializers.ModelSerializer):
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
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


#admin note serializer
class AdminNoteSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source='created_by.employee_id', read_only=True)
    created_by_role = serializers.CharField(source='created_by.role', read_only=True)
    
    class Meta:
        model = AdminNote
        fields = [
            'id',
            'employee',
            'note',
            'created_by',
            'created_by',
            'created_by_role',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']


#admin note 
class AdminNoteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminNote
        fields = ['employee', 'note']


#employee detail serializer
class EmployeeDetailSerializer(serializers.ModelSerializer):
    documents = EmployeeDocumentSerializer(many=True, read_only=True)
    media_files = EmployeeMediaSerializer(many=True, read_only=True)
    leave_records = LeaveListSerializer(source='leaves', many=True, read_only=True)
    salary_payment_history = SalaryPaymentSerializer(source='salary_payments', many=True, read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    profile_image_url = serializers.SerializerMethodField()  
    payment_status = serializers.SerializerMethodField()
    admin_notes = AdminNoteSerializer(many=True, read_only=True)
    salary = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    class Meta:
        model = CustomUser
        fields = [
            'id','email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'role', 'salary', 'payment_status', 'current_status', 'joining_date',
            'employee_id', 'department', 'designation', 'profile_image', 
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation',
            'address', 'city', 'state', 'postal_code', 'country',
            'date_of_birth', 'gender', 'profile_image_url',  
            'documents', 'media_files', 'leave_records', 'salary_payment_history',
            'admin_notes',    
        ]
    def get_payment_status(self, obj):
        from django.utils import timezone
        import calendar
        from datetime import date

        if not obj.joining_date:
            return "Unknown"

        today = timezone.now().date()
        
        current_date_iter = date(obj.joining_date.year, obj.joining_date.month, 1)
        
        end_date = date(today.year, today.month, 1)
        
        target_month = None
        target_year = None
        
        while current_date_iter <= end_date:
            m = current_date_iter.month
            y = current_date_iter.year
            
            is_paid = SalaryPayment.objects.filter(
                employee=obj,
                month=m,
                year=y,
                status__in=['paid', 'early_paid']
            ).exists()
            
            if not is_paid:
                target_month = m
                target_year = y
                break
            
            if current_date_iter.month == 12:
                current_date_iter = date(current_date_iter.year + 1, 1, 1)
            else:
                current_date_iter = date(current_date_iter.year, current_date_iter.month + 1, 1)

        if not target_month:
            current_payroll = SalaryPayment.objects.filter(
                employee=obj,
                month=today.month,
                year=today.year,
                status='early_paid'
            ).exists()
            
            next_month = (today.month % 12) + 1
            next_year = today.year + (1 if today.month == 12 else 0)
            next_payroll_is_early = SalaryPayment.objects.filter(
                employee=obj,
                month=next_month,
                year=next_year,
                status='early_paid'
            ).exists()

            if current_payroll or next_payroll_is_early:
                return "Early Salary Paid"
            return "Salary Paid"

        _, last_day_target_month = calendar.monthrange(target_year, target_month)
        payment_due_date = date(target_year, target_month, last_day_target_month)
        
        days_diff = (payment_due_date - today).days

        if days_diff < 0:
            return "Overdue"
        elif days_diff == 0:
            return "Pay Salary"
        elif 0 < days_diff <= 7:
            return "Payment date coming soon"
        
        return None

       

    
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
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    class Meta:
        model = CameraDepartment
        fields = [
            'id', 'client', 'client_name', 'uploaded_date', 'priority','link','employee_name'
        ]


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
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    class Meta:
        model = CameraDepartment
        fields = [
            'id', 'client', 'client_name',  
            'uploaded_date', 'priority', 'link','employee_name'
        ]


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
            'address_during_leave',
            'attachment',
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['employee'] = request.user
        return super().create(validated_data)


#Leave detail serializer
class LeaveDetailSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(
        source='employee.get_full_name', read_only=True
    )
    approved_by_name = serializers.CharField(
        source='approved_by.get_full_name', read_only=True
    )

    class Meta:
        model = LeaveManagement
        fields = '__all__'


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
            'address_during_leave', 
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