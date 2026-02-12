from django.urls import path
from .import views

urlpatterns = [
    path('clientverification-list/', views.ClientVerificationList.as_view()),
    path('close-month/', views.CloseMonthlyVerification.as_view(), name='close-month'),
    path('verified-list/', views.VerifiedClientList.as_view(), name='verified-list'),
]