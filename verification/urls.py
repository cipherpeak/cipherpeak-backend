from django.urls import path
from . import views

urlpatterns = [
    path('verifications/', views.ClientVerificationListCreateView.as_view(), name='verification-list-create'),

]