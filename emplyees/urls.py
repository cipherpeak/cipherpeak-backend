from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views


urlpatterns = [

    path('employees/create/', views.create_employee, name='create_employee'),
    path('employees/<int:employee_id>/update/', views.update_employee, name='update_employee'),
    path('employees/<int:employee_id>/delete/', views.delete_employee, name='delete_employee'),



    path('login/', views.login_view, name='login'),
    path('profile/', views.user_profile, name='user_profile'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<str:employee_id>/', views.employee_detail, name='employee_detail'),
    path('employees/me/full-details/', views.current_employee_full_details, name='current_employee_full_details'),
    path('documents/', views.employee_documents, name='employee_documents'),
    path('documents/<int:employee_id>/', views.employee_documents, name='employee_documents_by_id'),
    path('media/', views.employee_media, name='employee_media'),
    path('media/<int:employee_id>/', views.employee_media, name='employee_media_by_id'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]