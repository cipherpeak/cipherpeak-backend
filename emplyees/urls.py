from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views


urlpatterns = [
    # login url
    path('login/', views.login_view, name='login'),

    #Employee Creation
    path('employees/create/', views.create_employee, name='create_employee'),
    
    #Employee document_upload_url
    path('employees/upload_document/', views.EmployeeDocumentListCreateView.as_view(), name='upload_document'),

    #Employee media_upload_url
    path('employees/upload_media/', views.EmployeeMediaListCreateView.as_view(), name='upload_media'),

    # update employee details
    path('employees/<int:employee_id>/update/', views.update_employee, name='update_employee'),

    #delete employee
    path('employees/<int:employee_id>/delete/', views.delete_employee, name='delete_employee'),
    
    #user profile
    path('profile/', views.user_profile, name='user_profile'),

    #employee listing
    path('employees/', views.employee_list, name='employee_list'),
    
    #employee detail url
    path('employees/<str:employee_id>/', views.employee_detail, name='employee_detail'),
    
    #employee documents and media urls
    path('documents/', views.employee_documents, name='employee_documents'),
    path('documents/<int:employee_id>/', views.employee_documents, name='employee_documents_by_id'),
    path('media/', views.employee_media, name='employee_media'),
    path('media/<int:employee_id>/', views.employee_media, name='employee_media_by_id'),


    # JWT Token Refresh
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]




 