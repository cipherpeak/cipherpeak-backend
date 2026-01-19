from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views


urlpatterns = [
    # login url
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    #employee listing
    path('employees/', views.EmployeeListView.as_view(), name='employee_list'),
       
   #employee detail url
    path('employees/<str:employee_id>/', views.EmployeeDetailView.as_view(), name='employee_detail'),

    #Employee Creation
    path('employees/create/', views.EmployeeCreateView.as_view(), name='create_employee'),
    
    # update employee details
    path('employees/<int:employee_id>/update/', views.EmployeeUpdateView.as_view(), name='update_employee'),
    
    #Employee document_upload_url
    path('employees/upload_document/<int:employee_id>/', views.EmployeeDocumentCreateView.as_view(), name='upload_document'),

    #Employee media_upload_url
    path('employees/upload_media/<int:employee_id>/', views.EmployeeMediaCreateView.as_view(), name='upload_media'),
    
    # Delete paths
    path('employees/document/<int:pk>/delete/', views.EmployeeDocumentDeleteView.as_view(), name='delete_document'),
    path('employees/media/<int:pk>/delete/', views.EmployeeMediaDeleteView.as_view(), name='delete_media'),

    #delete employee
    path('employees/<int:employee_id>/delete/', views.EmployeeDeleteView.as_view(), name='delete_employee'),
    
 
    

    # JWT Token Refresh
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Camera Department
    path('camera-department/', views.CameraDepartmentListView.as_view(), name='camera_department_list'),
    path('camera-department/create/', views.CameraDepartmentCreateView.as_view(), name='camera_department_create'),
    path('camera-department/<int:pk>/', views.CameraDepartmentDetailView.as_view(), name='camera_department_detail'),

    # Leave Management
    path('leaves/', views.LeaveListView.as_view(), name='leave-list'),
    path('leaves/create/', views.LeaveCreateView.as_view(), name='leave-create'),
    path('leaves/<int:pk>/', views.LeaveDetailView.as_view(), name='leave-detail'),
    path('leaves/<int:pk>/process/', views.LeaveApprovalRejectView.as_view(), name='leave-process'),
    path('leaves/balance/', views.LeaveBalanceView.as_view(), name='leave-balance'),

    #Salary Payment
    path('salary-payment-history/', views.SalaryPaymentListView.as_view(), name='salary-payment-history'),
    path('process-salary-payment/<int:pk>/', views.ProcessSalaryPaymentView.as_view(), name='process-salary-payment'),
    path('payments/<int:id>/', views.PaymentDetailView.as_view(), name='payment-detail'),
    
   
]




 