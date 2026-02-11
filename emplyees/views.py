from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser  # Add this import
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from django.db.models import Prefetch
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import date
from .models import CustomUser, EmployeeDocument, EmployeeMedia, LeaveManagement, SalaryPayment, CameraDepartment, Announcement
from rest_framework.views import APIView
from .serializers import (
    EmployeeCreateSerializer,
    EmployeeUpdateSerializer,
    LoginSerializer, 
    EmployeeDetailSerializer,
    EmployeeDocumentSerializer,
    EmployeeDocumentCreateSerializer,
    EmployeeMediaSerializer,
    EmployeeMediaCreateSerializer,
    EmployeeListSerializer,
    CameraDepartmentListSerializer,
    CameraDepartmentCreateSerializer,
    CameraDepartmentDetailSerializer,
    LeaveCreateSerializer,
    LeaveListSerializer,
    LeaveDetailSerializer,
    LeaveUpdateSerializer,
    LeaveUpdateSerializer,
    SalaryPaymentSerializer,
    PaymentDetailSerializer,
    LeaveApprovalRejectSerializer,
    AnnouncementSerializer
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
                'user_info': {
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'username': user.username,
                    'id': user.id,
                    'user_type': user.user_type, 
                },
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }) 
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Successfully logged out"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Employee listing view
class EmployeeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employees = CustomUser.objects.filter(is_superuser=False,is_active=True).select_related()
        
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
            if not request.user.is_superuser and request.user.role not in ['director', 'managing_director']:
                return Response (
                    {'error': 'You do not have permission to create employees'},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = EmployeeCreateSerializer(data=request.data)
            
            if serializer.is_valid():
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
                
                try:
                    employee_data = {
                        'username': username,
                        'email': email,
                        'password': serializer.validated_data.get('password'), 
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
                        'is_active': True,
                    }
                    print("Employee data:", employee_data)
                    if 'profile_image' in request.FILES:
                        employee_data['profile_image'] = request.FILES['profile_image']
                        print("Profile image found and added to employee data")
                    
                    employee = CustomUser.objects.create_user(**employee_data)
                    
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
            
            if employee_id:
                employee = CustomUser.objects.get(id=employee_id, is_superuser=False)
            else:
                employee = CustomUser.objects.get(username=employee_id, is_superuser=False)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'Employee not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        employee = CustomUser.objects.filter(id=employee.id).prefetch_related(
            Prefetch('documents', queryset=EmployeeDocument.objects.all()),
            Prefetch('media_files', queryset=EmployeeMedia.objects.all()),
            Prefetch('leaves', queryset=LeaveManagement.objects.all().order_by('-start_date')),
            Prefetch('salary_payments', queryset=SalaryPayment.objects.all().order_by('-created_at'))
        ).first()
        
        serializer = EmployeeDetailSerializer(employee, context={'request': request})
        
        return Response(serializer.data)


# Delete employee view 
class EmployeeDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, employee_id):
        print("Delete employee called for ID:", employee_id)
        try:
           
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
class EmployeeDocumentCreateView(APIView):
    
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, employee_id):
    
        try:
            employee = CustomUser.objects.get(id=employee_id, is_superuser=False)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'Employee not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        if not request.user.is_superuser and request.user.role not in ['director', 'managing_director'] and request.user.id != employee.id:
            return Response (
                {'error': 'You do not have permission to upload documents for this employee'},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data.copy()
        serializer = EmployeeDocumentCreateSerializer(data=data, context={'request': request})
        
        if serializer.is_valid():
            
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
    

#employee media list create view
class EmployeeMediaCreateView(APIView):
   
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, employee_id):
        
        try:
            employee = CustomUser.objects.get(id=employee_id, is_superuser=False)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'Employee not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        if not request.user.is_superuser and request.user.role not in ['superuser', 'admin'] and request.user.id != employee.id:
            return Response (
                {'error': 'You do not have permission to upload media for this employee'},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data.copy()
        serializer = EmployeeMediaCreateSerializer(data=data, context={'request': request})
        
        if serializer.is_valid():
            
            media = serializer.save(user=employee)
            
            return Response({
                'message': 'Media file uploaded successfully',
                'media': EmployeeMediaSerializer(media, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# Employee document delete view
class EmployeeDocumentDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            document = EmployeeDocument.objects.get(pk=pk)
        except EmployeeDocument.DoesNotExist:
            return Response(
                {'error': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check permissions: owner or admin/hr/director
        is_owner = request.user == document.user
        is_admin = request.user.is_superuser or request.user.role in ['director', 'managing_director', 'admin', 'hr']

        if not (is_owner or is_admin):
             return Response(
                {'error': 'You do not have permission to delete this document'},
                status=status.HTTP_403_FORBIDDEN
            )

        document.delete()
        return Response(
            {'message': 'Document deleted successfully'},
            status=status.HTTP_200_OK
        )


# Employee media delete view
class EmployeeMediaDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            media = EmployeeMedia.objects.get(pk=pk)
        except EmployeeMedia.DoesNotExist:
            return Response(
                {'error': 'Media file not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check permissions: owner or admin/hr/director
        is_owner = request.user == media.user
        is_admin = request.user.is_superuser or request.user.role in ['director', 'managing_director', 'admin', 'hr']

        if not (is_owner or is_admin):
             return Response(
                {'error': 'You do not have permission to delete this media file'},
                status=status.HTTP_403_FORBIDDEN
            )

        media.delete()
        return Response(
            {'message': 'Media file deleted successfully'},
            status=status.HTTP_200_OK
        )



#salary payment list view
class SalaryPaymentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee_id = request.query_params.get('employee_id')
        
        if employee_id:
            # Check permissions: allow if searching for self OR if user has administrative role
            is_self = str(employee_id) == str(request.user.id)
            is_admin = request.user.is_superuser or request.user.role in ['admin', 'hr', 'manager', 'director']
            
            if not (is_self or is_admin):
                return Response(
                    {'error': 'You do not have permission to view other employees salary history'},
                    status=status.HTTP_403_FORBIDDEN
                )
            salary_payments = SalaryPayment.objects.filter(employee_id=employee_id)
        else:
            salary_payments = SalaryPayment.objects.filter(employee=request.user)
            
        serializer = SalaryPaymentSerializer(salary_payments, many=True)
        return Response(serializer.data)        
    



#process salary payment view
class ProcessSalaryPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            employee = CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)
            
        if not request.user.is_superuser and request.user.role not in ['admin', 'hr', 'manager', 'director']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            
        today = timezone.now().date()
        target_month = request.data.get('month')
        target_year = request.data.get('year')
        
        # Try to extract from date fields if month/year are missing
        if not target_month or not target_year:
            date_field = request.data.get('selected_date') or request.data.get('payment_date') or request.data.get('date')
            if date_field:
                try:
                    if isinstance(date_field, str):
                        # Handle ISO format or direct YYYY-MM-DD
                        from django.utils.dateparse import parse_date
                        parsed_d = parse_date(date_field.split('T')[0])
                        if parsed_d:
                            target_month = parsed_d.month
                            target_year = parsed_d.year
                except (ValueError, TypeError, IndexError):
                    pass

        # If still missing, default to current month (allows skipping past months)
        if not target_month or not target_year:
            target_month = today.month
            target_year = today.year
        
        target_month = int(target_month)
        target_year = int(target_year)

        # Validation: Block future months
        if (target_year > today.year) or (target_year == today.year and target_month > today.month):
             return Response({'error': f'Salary cannot be processed for {target_year}-{target_month:02}. Future month payments are not allowed.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validation: Joining date
        joining_date_start = date(employee.joining_date.year, employee.joining_date.month, 1)
        target_date_start = date(target_year, target_month, 1)
        if target_date_start < joining_date_start:
             return Response({'error': f'Cannot process payment for {target_month}/{target_year}. Employee joined on {employee.joining_date}'}, status=status.HTTP_400_BAD_REQUEST)

        existing_salary_payment = SalaryPayment.objects.filter(
            employee=employee,
            month=target_month,
            year=target_year,
            status__in=['paid', 'early_paid']
        ).exists()
        
        if existing_salary_payment:
            return Response({'error': f'Salary already paid for {target_month}/{target_year}'}, status=status.HTTP_400_BAD_REQUEST)
            
        base_salary = request.data.get('base_salary', employee.salary)
        incentives = request.data.get('incentives', 0)
        deductions = request.data.get('deductions', 0)
        remarks = request.data.get('remarks', '')
        payment_method = request.data.get('payment_method', 'bank_transfer')
        
        try:
            base_salary = float(base_salary) if base_salary else 0
            incentives = float(incentives)
            deductions = float(deductions)
            net_amount = base_salary + incentives - deductions
        except (ValueError, TypeError):
             return Response({'error': 'Invalid salary amounts'}, status=status.HTTP_400_BAD_REQUEST)
             
        import calendar
        _, last_day = calendar.monthrange(target_year, target_month)
        scheduled_date = date(target_year, target_month, last_day)

        if today < scheduled_date:
            payment_status_val = 'early_paid'
        else:
            payment_status_val = 'paid'
            
        salary_payment, created = SalaryPayment.objects.update_or_create(
            employee=employee,
            month=target_month,
            year=target_year,
            defaults={
                'base_salary': base_salary,
                'incentives': incentives,
                'deductions': deductions,
                'net_amount': net_amount,
                'scheduled_date': scheduled_date,
                'payment_date': timezone.now(),
                'status': payment_status_val,
                'payment_method': payment_method,
                'processed_by': request.user,
                'remarks': remarks
            }
        )
        
        # Record in Finance
        try:
            from finance.utils import record_system_expense
            record_system_expense(
                expense_type='employee_salaries',
                amount=net_amount,
                date=today,
                category_name='Employee Salaries',
                vendor_name=employee.get_full_name() or employee.username,
                remarks=f"Salary Payment for {employee.get_full_name() or employee.username} - {calendar.month_name[target_month]} {target_year}. {remarks}",
                reference_number=f"SAL-{salary_payment.id}",
                payment_method=payment_method,
                created_by=request.user
            )
        except Exception as e:
            print(f"Error recording finance expense: {str(e)}")

        return Response({
            'message': f'Salary payment for {target_month}/{target_year} processed successfully',
            'payroll_id': salary_payment.id,
            'status': salary_payment.get_status_display()
        }, status=status.HTTP_200_OK)



#salary payment detail view
class PaymentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            payment = SalaryPayment.objects.get(id=id)
            serializer = PaymentDetailSerializer(payment)
            return Response(serializer.data)
        except SalaryPayment.DoesNotExist:
            return Response(
                {"error": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND
            )



#camera department list view
class CameraDepartmentListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        
        if not request.user.is_superuser and request.user.role not in ['admin'] and request.user.user_type not in [
            'camera_department', 'hr', 'manager', 'content_creator', 'editor'
        ]:
            return Response(
                {'error': 'You do not have permission to view camera department projects'},
                status=status.HTTP_403_FORBIDDEN
            )

        projects = CameraDepartment.objects.all().select_related('client')
        client_id = request.GET.get('client')
        if client_id:
            projects = projects.filter(client_id=client_id)
            
        serializer = CameraDepartmentListSerializer(projects, many=True)
        
        # Check if user can create projects
        can_create = (
            request.user.is_superuser or 
            request.user.role in ['admin'] or 
            request.user.user_type in ['camera_department', 'content_creator', 'manager', 'hr', 'editor']
        )
        
        return Response({
            'projects': serializer.data,
            'can_create': can_create
        })


#camera department create view
class CameraDepartmentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        
        if not request.user.is_superuser and request.user.role not in ['admin'] and request.user.user_type not in [
            'camera_department', 'content_creator', 'manager', 'hr', 'editor'
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
        
        if not request.user.is_superuser and request.user.role not in ['admin'] and request.user.user_type not in [
            'camera_department', 'content_creator', 'manager', 'hr', 'editor'
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
    def delete(self, request, pk):
        project = self.get_object(pk)
        if not project:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if not request.user.is_superuser and request.user.role not in ['admin'] and request.user.user_type not in [
            'camera_department', 'content_creator', 'manager', 'hr', 'editor'
        ]:
            return Response(
                {'error': 'You do not have permission to delete camera department projects'},
                status=status.HTTP_403_FORBIDDEN
            )
        project.delete()
        return Response({'message': 'Project deleted successfully'})

#Leave create view 
class LeaveCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

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
        print("Leave serializer errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#Leave list view
class LeaveListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        status_filter = request.query_params.get('status')

        if user.is_superuser or user.role in ['manager', 'hr', 'admin', 'director']:
            leaves = LeaveManagement.objects.select_related(
                'employee', 'approved_by'
            )
        else:
            leaves = LeaveManagement.objects.filter(
                employee=user
            ).select_related('approved_by')

        if status_filter:
            status_list = [s.strip() for s in status_filter.split(',')]
            leaves = leaves.filter(status__in=status_list)

        serializer = LeaveListSerializer(leaves, many=True, context={'request': request})
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

        if (
            request.user != leave.employee and
            request.user.role not in ['manager', 'hr', 'admin', 'director']
        ):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = LeaveDetailSerializer(leave, context={'request': request})
        return Response(serializer.data)
        

    def put(self, request, pk):
        return self.update(request, pk, partial=False)

    def patch(self, request, pk):
        return self.update(request, pk, partial=True)

    def update(self, request, pk, partial):
        try:
            leave = LeaveManagement.objects.get(pk=pk)
        except LeaveManagement.DoesNotExist:
            return Response(
                {'error': 'Leave record not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        is_staff = request.user.role in ['manager', 'hr', 'admin', 'director']
        is_owner = request.user == leave.employee

        if not (is_staff or is_owner):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        if is_owner and not is_staff:
            if 'status' in request.data:
                 return Response(
                    {'error': 'You cannot change the status of your own leave application.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            if leave.status != 'pending':
                return Response(
                    {'error': 'You can only update leave applications that are still pending.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = LeaveUpdateSerializer(leave, data=request.data, partial=partial)
        if serializer.is_valid():
            if is_staff and 'status' in request.data:
                serializer.save(approved_by=request.user, approved_at=timezone.now())
            else:
                serializer.save()
            
            return Response(
                {
                    'message': 'Leave record updated successfully',
                    'leave': LeaveDetailSerializer(leave, context={'request': request}).data
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            leave = LeaveManagement.objects.get(pk=pk)
        except LeaveManagement.DoesNotExist:
            return Response(
                {'error': 'Leave record not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if (
            request.user != leave.employee and
            request.user.role not in ['manager', 'hr', 'admin', 'director']
        ):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        leave.delete()
        return Response(
            {'message': 'Leave record deleted successfully'},
            status=status.HTTP_200_OK
        )



class LeaveApprovalRejectView(APIView):

    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            leave = LeaveManagement.objects.get(pk=pk)
        except LeaveManagement.DoesNotExist:
            return Response(
                {'error': 'Leave application not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check permissions: only manager, hr, admin, or director can approve/reject
        if request.user.role not in ['manager', 'hr', 'admin', 'director'] and not request.user.is_superuser:
            return Response(
                {'error': 'You do not have permission to approve/reject leave applications'},
                status=status.HTTP_403_FORBIDDEN
            )

        if leave.status != 'pending':
            return Response(
                {'error': 'This leave application has already been processed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = LeaveApprovalRejectSerializer(leave, data=request.data)
        if serializer.is_valid():
            status_val = serializer.validated_data.get('status')
            
            if status_val not in ['approved', 'rejected']:
                return Response(
                    {'error': 'Invalid status. Must be approved or rejected.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if status_val == 'approved':
                leave.approved_by = request.user
                leave.approved_at = timezone.now()
            
            serializer.save()
            
            return Response(
                {
                    'message': f'Leave application {status_val} successfully',
                    'data': serializer.data
                },
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaveBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .models import LeaveBalance
        from .serializers import LeaveBalanceSerializer
        from django.utils import timezone
        
        balance, created = LeaveBalance.objects.get_or_create(
            employee=request.user,
            year=timezone.now().year
        )
        
        serializer = LeaveBalanceSerializer(balance)
        return Response(serializer.data)


# Announcement ViewSet
class AnnouncementViewSet(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        announcements = Announcement.objects.filter(is_active=True).select_related('created_by')
        serializer = AnnouncementSerializer(announcements, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        # Only admins/directors can post announcements
        if request.user.role not in ['admin', 'director', 'managing_director'] and not request.user.is_superuser:
            return Response(
                {'error': 'Only admins can post announcements'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AnnouncementSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AnnouncementDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Announcement.objects.get(pk=pk)
        except Announcement.DoesNotExist:
            return None

    def get(self, request, pk):
        announcement = self.get_object(pk)
        if not announcement:
            return Response({'error': 'Announcement not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AnnouncementSerializer(announcement, context={'request': request})
        return Response(serializer.data)

    def put(self, request, pk):
        announcement = self.get_object(pk)
        if not announcement:
            return Response({'error': 'Announcement not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user.role not in ['admin', 'director', 'managing_director'] and not request.user.is_superuser:
            return Response(
                {'error': 'Only admins can update announcements'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AnnouncementSerializer(announcement, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        announcement = self.get_object(pk)
        if not announcement:
            return Response({'error': 'Announcement not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user.role not in ['admin', 'director', 'managing_director'] and not request.user.is_superuser:
            return Response(
                {'error': 'Only admins can delete announcements'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        announcement.is_active = False # Soft delete
        announcement.save()
        return Response({'message': 'Announcement deleted successfully'})


class EmployeePasswordResetView(APIView):
    permission_classes =[IsAuthenticated]  
    def post(self, request, pk):
        if not request.user.is_superuser and request.user.role not in ['admin', 'director', 'manager']:
            return Response(
                {'error': 'You do not have permission to reset passwords'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            # Get the user (employee) by ID
            user = get_object_or_404(CustomUser, pk=pk)
            
            # Get the new password from the request body
            new_password = request.data.get('password')
            
            if not new_password:
                return Response(
                    {'error': 'Password is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if len(new_password) < 5:
                return Response(
                    {'error': 'Password must be at least 5 characters long'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Set the new password
            user.set_password(new_password)
            user.save()
            
            return Response(
                {'message': 'Password updated successfully'}, 
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )