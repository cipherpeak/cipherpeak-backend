from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.VerificationDashboardView.as_view(), name='verification-dashboard'),
    
    # Posted content management
    path('add-posted-content/', views.AddPostedContentView.as_view(), name='add-posted-content'),
    path('remove-posted-content/', views.RemovePostedContentView.as_view(), name='remove-posted-content'),
    path('delete-posted-content/<int:verification_id>/', views.DeletePostedContentView.as_view(), name='delete-posted-content'),
    
    # Verification
    path('verify-client/', views.VerifyClientMonthView.as_view(), name='verify-client'),
    path('bulk-update-status/', views.BulkUpdateVerificationStatusView.as_view(), name='bulk-update-status'),
    
    # Quota management
    path('update-quota/', views.UpdateQuotaView.as_view(), name='update-quota'),
    
    # Details
    path('client-content/<int:client_id>/', views.GetClientPostedDetailsView.as_view(), name='client-content'),
]