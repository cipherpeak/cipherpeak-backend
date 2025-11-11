# client/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Client URLs
    path('create/', views.ClientListCreateView.as_view(), name='client-list-create'),
    path('create/<int:id>/', views.ClientDetailView.as_view(), name='client-detail'),
    path('clients/stats/', views.ClientStatsView.as_view(), name='client-stats'),
    
    # Client Document URLs
    path('documents/', views.ClientDocumentListCreateView.as_view(), name='client-document-list-create'),
    path('documents/<int:id>/', views.ClientDocumentDetailView.as_view(), name='client-document-detail'),

    path('earlypaid/<int:id>/mark-early-payment/', views.ClientMarkEarlyPaymentView.as_view(), name='client-mark-early-payment'),
    path('clients/<int:id>/payment-timeline/', views.ClientPaymentTimelineView.as_view(), name='client-payment-timeline'),
    path('clients/early-payments/', views.ClientEarlyPaymentsView.as_view(), name='client-early-payments'),
    path('clients/payment-analytics/', views.client_payment_analytics, name='client-payment-analytics'),
]