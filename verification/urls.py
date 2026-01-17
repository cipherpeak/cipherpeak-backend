from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.VerificationDashboardView.as_view(), name='verification-dashboard'),
    path('submit/', views.ContentVerificationSubmitView.as_view(), name='verification-submit'),
    path('pending/', views.PendingVerificationsView.as_view(), name='pending-verifications'),
    path('clients/<int:pk>/content-targets/',views.ClientContentTargetsView.as_view(), name='client-content-targets'),
    path('payment-status/',views.PaymentStatusCheckView.as_view(),name='verification-payment-status'),
]