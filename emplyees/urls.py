from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views


urlpatterns = [
    # login url
    path('login/', views.LoginView.as_view(), name='login'),

    #employee listing
    path('employees/', views.EmployeeListView.as_view(), name='employee_list'),
       
    #Employee Creation
    path('employees/create/', views.EmployeeCreateView.as_view(), name='create_employee'),

    # update employee details
    path('employees/<int:employee_id>/update/', views.EmployeeUpdateView.as_view(), name='update_employee'),
    
    #Employee document_upload_url
    path('employees/upload_document/<int:employee_id>/', views.EmployeeDocumentListCreateView.as_view(), name='upload_document'),

    #Employee media_upload_url
    path('employees/upload_media/<int:employee_id>/', views.EmployeeMediaListCreateView.as_view(), name='upload_media'),

    #delete employee
    path('employees/<int:employee_id>/delete/', views.EmployeeDeleteView.as_view(), name='delete_employee'),
    
    #employee detail url
    path('employees/<str:employee_id>/', views.EmployeeDetailView.as_view(), name='employee_detail'),
    

    # JWT Token Refresh
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]




 