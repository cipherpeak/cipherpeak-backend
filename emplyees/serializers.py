from rest_framework import serializers
from .models import CustomUser, EmployeeDocument, EmployeeMedia, LeaveManagement, SalaryHistory, CameraDepartment, AdminNote
from django.contrib.auth import authenticate



#login serializer
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    data['user'] = user
                else:
                    raise serializers.ValidationError('User account is disabled.')
            else:
                raise serializers.ValidationError('Unable to log in with provided credentials.')
        else:
            raise serializers.ValidationError('Must include username and password.')
        return data


#employee list serializer
class EmployeeListSerializer(serializers.ModelSerializer):
    profile_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'role', 'current_status', 'department',
            'designation','profile_image_url',
            
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
            'profile_image',  # Add profile_image here
        ]
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'role': {'required': True},
            'current_status': {'required': True},
            'joining_date': {'required': True},
            'profil e_image': {'required': False},  # Make profile_image optional
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
        """Validate profile image file"""
        if value:
            # Check file size (e.g., 5MB limit)
            max_size = 5 * 1024 * 1024  # 5MB
            if value.size > max_size:
                raise serializers.ValidationError("Profile image size cannot exceed 5MB.")
            
            # Check file type
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
        """Validate profile image file"""
        if value:
            # Check file size (e.g., 5MB limit)
            max_size = 5 * 1024 * 1024  # 5MB
            if value.size > max_size:
                raise serializers.ValidationError("Profile image size cannot exceed 5MB.")
            
            # Check file type
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp']
            extension = value.name.split('.')[-1].lower()
            if extension not in valid_extensions:
                raise serializers.ValidationError(
                    f"Unsupported file format. Supported formats: {', '.join(valid_extensions)}"
                )
        return value


#employee document serializer
class EmployeeDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = EmployeeDocument
        fields = [
            'id', 'document_type','file_url'
        ]
        
    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None


#employee media serializer
class EmployeeMediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = EmployeeMedia
        fields = [
            'id', 'media_type','file_url'
        ]
       
    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None

#Leave list serializer
class LeaveListSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(
        source='employee.get_full_name', read_only=True
    )
    approved_by_name = serializers.CharField(
        source='approved_by.get_full_name', read_only=True
    )

    class Meta:
        model = LeaveManagement
        fields = [
            'id',
            'employee_name',
            'category',
            'start_date',
            'end_date',
            'total_days',
            'status',
            'approved_by_name',
            'created_at',
        ]


#salary history serializer
class SalaryHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryHistory
        fields = [
            'id', 'salary', 'incentive',
            'reason', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


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

class AdminNoteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminNote
        fields = ['employee', 'note']


#employee detail serializer
class EmployeeDetailSerializer(serializers.ModelSerializer):
    documents = EmployeeDocumentSerializer(many=True, read_only=True)
    media_files = EmployeeMediaSerializer(many=True, read_only=True)
    leave_records = LeaveListSerializer(source='leaves', many=True, read_only=True)
    salary_history = SalaryHistorySerializer(many=True, read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    profile_image_url = serializers.SerializerMethodField()  
    payment_status = serializers.SerializerMethodField()
    admin_notes = AdminNoteSerializer(many=True, read_only=True)
    class Meta:
        model = CustomUser
        fields = [
            'id','email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'role', 'salary', 'payment_status', 'current_status', 'joining_date',
            'employee_id', 'department', 'designation', 'profile_image', 
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation',
            'address', 'city', 'state', 'postal_code', 'country',
            'date_of_birth', 'gender', 'profile_image_url',  
            'documents', 'media_files', 'leave_records', 'salary_history',
            'admin_notes',    
        ]
    
    def get_payment_status(self, obj):
        from django.utils import timezone
        import calendar
        
        today = timezone.now().date()
        
        # Check if salary history exists for current month and year
        has_paid = obj.salary_history.filter(
            created_at__year=today.year, 
            created_at__month=today.month
        ).exists()
        
        if has_paid:
            return "Paid"
            
        today = timezone.now().date()
        if not obj.joining_date:
            return "Unknown"
            
        joining_day = obj.joining_date.day
        
        # Calculate payment due date for current month
        try:
            payment_due_date = today.replace(day=joining_day)
        except ValueError:
            # Handle shorter months
            last_day = calendar.monthrange(today.year, today.month)[1]
            payment_due_date = today.replace(day=last_day)
            
        days_diff = (payment_due_date - today).days
        
        if days_diff <= 0:
            return "Payment Due" # Date passed for this month or is today
        elif days_diff <= 5:
            return "Payment date reaching soon"
        else:
            return "Pending"
    
    def get_profile_image_url(self, obj):
        """Get the full URL for the profile image"""
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
            'status', 
            'rejection_reason'
        ]
        read_only_fields = ['employee', 'created_at', 'updated_at']

    def validate(self, data):
        """
        Validate that only authorized users can change the status.
        Approval logic should ideally be handled here or in the view.
        """
        return data




