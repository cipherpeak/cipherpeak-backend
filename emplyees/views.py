from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser  # Add this import
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from django.db.models import Prefetch
from .models import CustomUser, EmployeeDocument, EmployeeMedia, LeaveRecord, SalaryHistory
from .serializers import (
    EmployeeCreateSerializer,
    UserSerializer, 
    LoginSerializer, 
    EmployeeDetailSerializer,
    
    EmployeeMediaSerializer,
    LeaveRecordSerializer,
    SalaryHistorySerializer
)
# login view 
@api_view(['POST']) 
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid(): 
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': user.role,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


# Employee listing view
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employee_list(request):
    """
    Get list of all employees (non-superusers) with basic details
    """
    employees = CustomUser.objects.filter(is_superuser=False,is_active=True).select_related()
    
    # Optional query parameters for filtering
    role = request.GET.get('role')
    status_filter = request.GET.get('status')
    department = request.GET.get('department')
    
    if role:
        employees = employees.filter(role=role)
    if status_filter:
        employees = employees.filter(current_status=status_filter)
    if department:
        employees = employees.filter(department__icontains=department)
    
    serializer = UserSerializer(employees, many=True)
    return Response({
        'count': employees.count(),
        'employees': serializer.data
    })



#Employee detail_view
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employee_detail(request, employee_id):
    """
    Get full details of a specific employee by ID or username
    """
    try:
       
        # Try to get by ID first, then by username
        if employee_id.isdigit():
            employee = CustomUser.objects.get(id=employee_id, is_superuser=False)
        else:
            employee = CustomUser.objects.get(username=employee_id, is_superuser=False)
    except CustomUser.DoesNotExist:
        return Response(
            {'error': 'Employee not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Prefetch related data for better performance
    employee = CustomUser.objects.filter(id=employee.id).prefetch_related(

        Prefetch('documents', queryset=EmployeeDocument.objects.all()),
        Prefetch('media_files', queryset=EmployeeMedia.objects.all()),
        Prefetch('leave_records', queryset=LeaveRecord.objects.all().order_by('-start_date')),
        Prefetch('salary_history', queryset=SalaryHistory.objects.all().order_by('-effective_from'))
    ).first()
    
    serializer = EmployeeDetailSerializer(employee,context={'request':request})
    
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employee_documents(request, employee_id=None):
    """
    Get documents for a specific employee or current user
    """
    if employee_id and request.user.is_superuser:
        # Admin can view any employee's documents
        try:
            employee = CustomUser.objects.get(id=employee_id, is_superuser=False)
            documents = employee.documents.all()
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'Employee not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        # Regular users can only view their own documents
        documents = request.user.documents.all()
    
    serializer = EmployeeCreateDocumentSerializer(documents, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employee_media(request, employee_id=None):
    """
    Get media files for a specific employee or current user
    """
    if employee_id and request.user.is_superuser:
        # Admin can view any employee's media
        try:
            employee = CustomUser.objects.get(id=employee_id, is_superuser=False)
            media_files = employee.media_files.all()
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'Employee not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        # Regular users can only view their own media
        media_files = request.user.media_files.all()
    
    serializer = EmployeeMediaSerializer(media_files, many=True)
    return Response(serializer.data)


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import EmployeeMedia
from .serializers import EmployeeDocumentSerializer  

class EmployeeDocumentCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        print(request.data,"this is request data")
        # Add user to data
        data = request.data.copy()
        
        # Create serializer with data
        serializer = EmployeeDocumentSerializer(data=data)
        
        if serializer.is_valid():
            # Save with current user
            document = serializer.save(user=request.user)
            
            return Response({
                'status': 'success',
                'message': 'Document uploaded successfully',
                'document': {
                    'id': document.id,
                    'title': document.title,
                    'media_type': document.media_type,
                    'media_type_display': document.get_media_type_display(),
                    'file_url': request.build_absolute_uri(document.file.url),
                    'uploaded_at': document.uploaded_at
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    









@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])  # Add this decorator
def create_employee(request):
    """
    Create a new employee with profile image support
    """
    try:
        # Check if user has permission to create employees
        if not request.user.is_superuser and request.user.role not in ['director', 'managing_director', 'manager']:
            return Response(
                {'error': 'You do not have permission to create employees'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Debug: Check what data is being received
        print("Request data:", request.data)
        print("Request FILES:", request.FILES)
        
        serializer = EmployeeCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Check if username or email already exists
            username = serializer.validated_data.get('username')
            email = serializer.validated_data.get('email')
            
            if CustomUser.objects.filter(username=username).exists():
                return Response(
                    {'error': 'Username already exists'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if CustomUser.objects.filter(email=email).exists():
                return Response(
                    {'error': 'Email already exists'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create the user with all data including profile_image
            try:
                employee_data = {
                    'username': username,
                    'email': email,
                    'password': 'defaultpassword123',  # Default password
                    'first_name': serializer.validated_data.get('first_name', ''),
                    'last_name': serializer.validated_data.get('last_name', ''),
                    'phone_number': serializer.validated_data.get('phone_number'),
                    'date_of_birth': serializer.validated_data.get('date_of_birth'),
                    'gender': serializer.validated_data.get('gender'),
                    'address': serializer.validated_data.get('address'),
                    'city': serializer.validated_data.get('city'),
                    'state': serializer.validated_data.get('state'),
                    'postal_code': serializer.validated_data.get('postal_code'),
                    'country': serializer.validated_data.get('country'),
                    'emergency_contact_name': serializer.validated_data.get('emergency_contact_name'),
                    'emergency_contact_phone': serializer.validated_data.get('emergency_contact_phone'),
                    'emergency_contact_relation': serializer.validated_data.get('emergency_contact_relation'),
                    'employee_id': serializer.validated_data.get('employee_id'),
                    'role': serializer.validated_data.get('role', 'employee'),
                    'department': serializer.validated_data.get('department'),
                    'designation': serializer.validated_data.get('designation'),
                    'salary': serializer.validated_data.get('salary'),
                    'current_status': serializer.validated_data.get('current_status', 'active'),
                    'joining_date': serializer.validated_data.get('joining_date'),
                }
                
                # Add profile_image if it exists in the request
                if 'profile_image' in request.FILES:
                    employee_data['profile_image'] = request.FILES['profile_image']
                    print("Profile image found and added to employee data")
                
                employee = CustomUser.objects.create_user(**employee_data)
                
                # Return the created employee data with profile image URL
                response_serializer = UserSerializer(employee, context={'request': request})
                return Response(
                    {
                        'message': 'Employee created successfully',
                        'employee': response_serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )
                
            except Exception as e:
                print(f"Error creating employee: {str(e)}")
                return Response(
                    {'error': f'Error creating employee: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        else:
            print("Serializer errors:", serializer.errors)
            return Response(
                {'error': 'Invalid data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        print(f"Server error in create_employee: {str(e)}")
        return Response(
            {'error': f'Server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])  
def update_employee(request, employee_id):
    """
    Update employee details with profile image support
    """
    try:
        # Check if user has permission to update employees
        if not request.user.is_superuser and request.user.role not in ['director', 'managing_director', 'manager']:
            return Response(
                {'error': 'You do not have permission to update employees'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            employee = CustomUser.objects.get(id=employee_id, is_superuser=False)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'Employee not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Debug: Check what data is being received
        print("Update request data:", request.data)
        print("Update request FILES:", request.FILES)

        serializer = EmployeeCreateSerializer(
            employee, 
            data=request.data, 
            partial=True  # Allow partial updates for PATCH
        )
        
        if serializer.is_valid():
            # Check for unique fields if they're being updated
            if 'username' in request.data:
                new_username = request.data['username']
                if CustomUser.objects.filter(username=new_username).exclude(id=employee_id).exists():
                    return Response(
                        {'error': 'Username already exists'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
           
                
            
            if 'email' in request.data:
                new_email = request.data['email']
                if CustomUser.objects.filter(email=new_email).exclude(id=employee_id).exists():
                    return Response(
                        {'error': 'Email already exists'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Save the serializer (this will handle the profile_image)
            serializer.save()
            
            
            response_serializer = UserSerializer(employee, context={'request': request})
            return Response(
                {
                    'message': 'Employee updated successfully',
                    'employee': response_serializer.data
                },
                status=status.HTTP_200_OK
            )
        else:
            print("Update serializer errors:", serializer.errors)
            return Response(
                {'error': 'Invalid data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
            
    except Exception as e:
        print(f"Server error in update_employee: {str(e)}")
        return Response(
            {'error': f'Server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    
    
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_employee(request, employee_id):
    print("Delete employee called for ID:", employee_id)
    """
    Delete an employee
    """
    try:
        # Check if user has permission to delete employees
        if not request.user.is_superuser and request.user.role not in ['director', 'managing_director']:
            return Response(
                {'error': 'You do not have permission to delete employees'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            employee = CustomUser.objects.get(id=employee_id, is_superuser=False)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'Employee not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Prevent users from deleting themselves
        if employee.id == request.user.id:
            return Response(
                {'error': 'You cannot delete your own account'},
                status=status.HTTP_400_BAD_REQUEST
            )

       
        employee.is_active = False
        employee.save()
        
        
        return Response(
            {'message': 'Employee deleted successfully'},
            status=status.HTTP_200_OK
        )
            
    except Exception as e:
        return Response(
            {'error': f'Server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )







# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def current_employee_full_details(request):
#     """
#     Get full details of the currently authenticated employee
#     """
#     employee = CustomUser.objects.filter(id=request.user.id).prefetch_related(
#         Prefetch('documents', queryset=EmployeeDocument.objects.all()),
#         Prefetch('media_files', queryset=EmployeeMedia.objects.all()),
#         Prefetch('leave_records', queryset=LeaveRecord.objects.all().order_by('-start_date')),
#         Prefetch('salary_history', queryset=SalaryHistory.objects.all().order_by('-effective_from'))
#     ).first()
    
#     serializer = EmployeeDetailSerializer(employee)
#     return Response(serializer.data)

