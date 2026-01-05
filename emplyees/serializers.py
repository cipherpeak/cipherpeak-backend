from rest_framework import serializers
from .models import CustomUser, EmployeeDocument, EmployeeMedia, LeaveRecord, SalaryHistory
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
            'designation', 'employee_id','profile_image', 'profile_image_url',
            
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


#leave record serializer
class LeaveRecordSerializer(serializers.ModelSerializer):
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    
    class Meta:
        model = LeaveRecord
        fields = [
            'id', 'leave_type', 'start_date', 'end_date', 
            'reason', 'status', 'applied_on', 'approved_by', 
            'approved_by_name', 'approved_on'
        ]
        read_only_fields = ['applied_on', 'approved_on']


#salary history serializer
class SalaryHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    
    class Meta:
        model = SalaryHistory
        fields = [
            'id', 'salary', 'effective_from', 'effective_to',
            'reason', 'changed_by', 'changed_by_name', 'changed_at'
        ]
        read_only_fields = ['changed_at']


#employee detail serializer
class EmployeeDetailSerializer(serializers.ModelSerializer):
    documents = EmployeeDocumentSerializer(many=True, read_only=True)
    media_files = EmployeeMediaSerializer(many=True, read_only=True)
    leave_records = LeaveRecordSerializer(many=True, read_only=True)
    salary_history = SalaryHistorySerializer(many=True, read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    profile_image_url = serializers.SerializerMethodField()  
    
    class Meta:
        model = CustomUser
        fields = [
            'id','email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'role', 'salary', 'current_status', 'joining_date',
            'employee_id', 'department', 'designation', 'profile_image', 
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation',
            'address', 'city', 'state', 'postal_code', 'country',
            'date_of_birth', 'gender', 'profile_image_url',  
            'documents', 'media_files', 'leave_records', 'salary_history',    
        ]
    
    def get_profile_image_url(self, obj):
        """Get the full URL for the profile image"""
        if obj.profile_image and hasattr(obj.profile_image, 'url'):
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.profile_image.url)
            return obj.profile_image.url
        return None










# Update your existing UserSerializer
class UserSerializer(serializers.ModelSerializer):
    profile_image_url = serializers.SerializerMethodField()  # Add this field
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email','phone_number', 'role', 'current_status', 'department',
            'designation', 'employee_id', 'joining_date', 'salary',
            'date_of_birth', 'gender', 'address', 'city', 'state',
            'postal_code', 'country', 'emergency_contact_name',
            'emergency_contact_phone', 'emergency_contact_relation',
            'profile_image', 'profile_image_url', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_profile_image_url(self, obj):
        """Get the full URL for the profile image"""
        if obj.profile_image and hasattr(obj.profile_image, 'url'):
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.profile_image.url)
            return obj.profile_image.url
        return None