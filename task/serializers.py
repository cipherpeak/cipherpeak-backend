from rest_framework import serializers
from .models import Task
from emplyees.models import CustomUser
from clientapp.serializers import ClientSerializer  

#assignee serializer
class AssigneeSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    designation = serializers.CharField(read_only=True)
    department = serializers.CharField(read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 
            'username', 
            'email', 
            'first_name', 
            'last_name', 
            'full_name',
            'role',
            'designation',
            'department',
            'employee_id',
            'phone_number',
        ]
       
    def get_full_name(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name if name else obj.username


# task create serializer
class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id',
            'title', 
            'description', 
            'assignee', 
            'client', 
            'status', 
            'priority',
            'task_type', 
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# task update serializer
class TaskUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'assignee',
            'client',  
            'status',
            'priority',
            'task_type',
        ]
        read_only_fields = ['id']


# task detail serializer
class TaskDetailSerializer(serializers.ModelSerializer):
    assignee_details = AssigneeSerializer(source='assignee', read_only=True)
    created_by_details = AssigneeSerializer(source='created_by', read_only=True)
    client_details = ClientSerializer(source='client', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 
            'title', 
            'description', 
            'assignee', 
            'assignee_details',
            'client',  
            'client_details', 
            'status', 
            'status_display',
            'priority', 
            'priority_display',
            'task_type',
            'task_type_display',
            'completed_at', 
            'created_by', 
            'created_by_details', 
            'created_at',
            'updated_at'
        ]
       

# task list serializer
class TaskListSerializer(serializers.ModelSerializer):
    assignee_details = AssigneeSerializer(source='assignee', read_only=True)
    client_details = ClientSerializer(source='client', read_only=True)
    assignee_name = serializers.SerializerMethodField()
    assignee_designation = serializers.CharField(source='assignee.designation', read_only=True)
    client_name = serializers.CharField(source='client.client_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'assignee',
            'assignee_details',
            'client',
            'client_details',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'task_type',
            'assignee_name',
            'assignee_designation',
            'client_name',
            'created_at'
        ]
    
    def get_assignee_name(self, obj):
        if obj.assignee:
            name = f"{obj.assignee.first_name} {obj.assignee.last_name}".strip()
            return name if name else obj.assignee.username
        return "Unassigned"
