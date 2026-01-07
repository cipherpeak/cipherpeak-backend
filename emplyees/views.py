from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser  # Add this import
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from django.db.models import Prefetch
from .models import CustomUser, EmployeeDocument, EmployeeMedia, LeaveManagement, SalaryHistory, CameraDepartment
from rest_framework.views import APIView
from .serializers import (
    EmployeeCreateSerializer,
    EmployeeUpdateSerializer,
    LoginSerializer, 
    EmployeeDetailSerializer,
    EmployeeDocumentSerializer, 
    EmployeeMediaSerializer,
    SalaryHistorySerializer,
    EmployeeListSerializer,
    CameraDepartmentListSerializer,
    CameraDepartmentCreateSerializer,
    CameraDepartmentDetailSerializer,
    LeaveCreateSerializer,
    LeaveListSerializer,
    LeaveDetailSerializer,
)

# login view 
class LoginView(APIView):
    def post(self, request):
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


        
# Employee listing view
class EmployeeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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
        
        serializer = EmployeeListSerializer(employees, many=True, context={'request': request})
        return Response({
            'count': employees.count(),
            'employees': serializer.data
        })



# Create employee view
class EmployeeCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        try:
            # Check if user has permission to create employees
            if not request.user.is_superuser and request.user.role not in ['director', 'managing_director']:
                return Response (
                    {'error': 'You do not have permission to create employees'},
                    status=status.HTTP_403_FORBIDDEN
                )

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
                    return Response(
                        {
                            'message': 'Employee created successfully',
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
    

    
# Update employee view
class EmployeeUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def patch(self, request, employee_id):
        return self.update(request, employee_id, partial=True)

    def put(self, request, employee_id):
        return self.update(request, employee_id, partial=False)

    def update(self, request, employee_id, partial=False):
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
            
            serializer = EmployeeUpdateSerializer(
                employee, 
                data=request.data, 
                partial=partial
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
                
                serializer.save()
            
                return Response(
                    {
                        'message': 'Employee updated successfully',
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



#employee detail view   
class EmployeeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id)  :
        try:
            # Try to get by ID first, then by username
            if employee_id:
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
        
        serializer = EmployeeDetailSerializer(employee, context={'request': request})
        
        return Response(serializer.data)



# Delete employee view 
class EmployeeDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, employee_id):
        print("Delete employee called for ID:", employee_id)
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



#employee document upload view
class EmployeeDocumentListCreateView(APIView):
    
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, employee_id):
        """
        Create a new document for the specified employee
        """
        try:
            employee = CustomUser.objects.get(id=employee_id, is_superuser=False)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'Employee not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user has permission to upload documents for this employee
        # Allow admins or the employee themselves to upload
        if not request.user.is_superuser and request.user.role not in ['director', 'managing_director'] and request.user.id != employee.id:
            return Response (
                {'error': 'You do not have permission to upload documents for this employee'},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data.copy()
        serializer = EmployeeDocumentSerializer(data=data, context={'request': request})
        
        if serializer.is_valid():
            # Save with targeted employee
            document = serializer.save(user=employee)
            
            return Response({
                'status': 'success',
                'message': 'Document uploaded successfully',
                'document': EmployeeDocumentSerializer(document, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    


class EmployeeMediaListCreateView(APIView):
   
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, employee_id):
        """
        Create a new media file for the specified employee
        """
        try:
            employee = CustomUser.objects.get(id=employee_id, is_superuser=False)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'Employee not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user has permission to upload media for this employee
        if not request.user.is_superuser and request.user.role not in ['superuser', 'admin'] and request.user.id != employee.id:
            return Response (
                {'error': 'You do not have permission to upload media for this employee'},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data.copy()
        serializer = EmployeeMediaSerializer(data=data, context={'request': request})
        
        if serializer.is_valid():
            # Save with targeted employee
            media = serializer.save(user=employee)
            
            return Response({
                'message': 'Media file uploaded successfully',
                'media': EmployeeMediaSerializer(media, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    


#camera department list view
class CameraDepartmentListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Permission check for listing
        if not request.user.is_superuser and request.user.role not in ['admin'] and request.user.user_type not in [
            'camera_department', 'hr', 'manager', 'content_creator', 'editor'
        ]:
            return Response(
                {'error': 'You do not have permission to view camera department projects'},
                status=status.HTTP_403_FORBIDDEN
            )

        projects = CameraDepartment.objects.all().select_related('client')
        
        # Filter by client if provided
        client_id = request.GET.get('client')
        if client_id:
            projects = projects.filter(client_id=client_id)
            
        serializer = CameraDepartmentListSerializer(projects, many=True)
        return Response(serializer.data)



#camera department create view
class CameraDepartmentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Permission check for creation
        if not request.user.is_superuser and request.user.role not in ['admin'] and request.user.user_type not in [
            'camera_department', 'content_creator', 'manager', 'hr'
        ]:
            return Response(
                {'error': 'You do not have permission to create camera department projects'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = CameraDepartmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(employee=request.user)
            return Response("project created successfully", status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



#camera department detail view
class CameraDepartmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return CameraDepartment.objects.get(pk=pk)
        except CameraDepartment.DoesNotExist:
            return None

    def get(self, request, pk):
        project = self.get_object(pk)
        if not project:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CameraDepartmentDetailSerializer(project)
        return Response(serializer.data)

    def put(self, request, pk):
        project = self.get_object(pk)
        if not project:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Permission check for update
        if not request.user.is_superuser and request.user.role not in ['admin'] and request.user.user_type not in [
            'camera_department', 'content_creator', 'manager', 'hr'
        ]:
            return Response(
                {'error': 'You do not have permission to update camera department projects'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CameraDepartmentCreateSerializer(project, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#Leave create view 
class LeaveCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = LeaveCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save(employee=request.user)
            return Response(
                {'message': 'Leave applied successfully'},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#Leave list view
class LeaveListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role in ['manager', 'hr', 'admin', 'director']:
            leaves = LeaveManagement.objects.select_related(
                'employee', 'approved_by'
            )
        else:
            leaves = LeaveManagement.objects.filter(
                employee=user
            ).select_related('approved_by')

        serializer = LeaveListSerializer(leaves, many=True)
        return Response(serializer.data)


#Leave detail view
class LeaveDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            leave = LeaveManagement.objects.select_related(
                'employee', 'approved_by'
            ).get(pk=pk)
        except LeaveManagement.DoesNotExist:
            return Response(
                {'error': 'Leave record not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Permission check
        if (
            request.user != leave.employee and
            request.user.role not in ['manager', 'hr', 'admin', 'director']
        ):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = LeaveDetailSerializer(leave)
        return Response(serializer.data)
