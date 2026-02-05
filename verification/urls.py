from django.urls import path
from . import views

urlpatterns = [

    path('verification-dashboard/', views.VerificationDashboardView.as_view(), name='verification-dashboard'),
    path('mark-client-verified/', views.MarkClientVerifiedView.as_view(), name='mark-client-verified'),
]