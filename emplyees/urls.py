from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views


urlpatterns = [
    # login url
    path('login/', views.login_view, name='login'),

    #Employee Creation
    path('employees/create/', views.create_employee, name='create_employee'),

    path('employees/upload_document/', views.EmployeeDocumentListCreateView.as_view(), name='upload_document'),
    path('employees/upload_media/', views.EmployeeMediaListCreateView.as_view(), name='upload_media'),
    # update employee details
    path('employees/<int:employee_id>/update/', views.update_employee, name='update_employee'),

    #delete employee
    path('employees/<int:employee_id>/delete/', views.delete_employee, name='delete_employee'),

    path('profile/', views.user_profile, name='user_profile'),

    #employee listing
    path('employees/', views.employee_list, name='employee_list'),
    
    #employee detail url
    path('employees/<str:employee_id>/', views.employee_detail, name='employee_detail'),
    
    
    # path('documents/', views.employee_documents, name='employee_documents'),
    # path('documents/<int:employee_id>/', views.employee_documents, name='employee_documents_by_id'),
    # path('media/', views.employee_media, name='employee_media'),
    # path('media/<int:employee_id>/', views.employee_media, name='employee_media_by_id'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]




 # path('employees/me/full-details/', views.current_employee_full_details, name='current_employee_full_details'),