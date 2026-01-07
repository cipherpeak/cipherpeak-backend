# client/urls.py
from django.urls import path
from . import views

urlpatterns = [
    #create client URL
    path('create/', views.ClientCreateView.as_view(), name='client-create'),

    #client detail URL
    path('clients/details/<int:id>/', views.ClientDetailView.as_view(), name='client-detail'),

    # Client list url
    path('clients/', views.ClientListView.as_view(), name='client-list'),

    #client update url
    path('clients/<int:id>/update/', views.ClientUpdateView.as_view(), name='client-update'),

    #client upload document URL
    path('clients/<int:id>/upload-document/', views.ClientDocumentUploadView.as_view(), name='client-upload-document'),

    #client delete url
    path('clients/delete/<int:id>/', views.ClientDeleteView.as_view(), name='delete_client'),






    # Client Statistics URL
    path('clients/stats/', views.ClientStatsView.as_view(), name='client-stats'),
    path('earlypaid/<int:id>/mark-early-payment/', views.ClientMarkEarlyPaymentView.as_view(), name='client-mark-early-payment'),
    path('clients/<int:id>/payment-timeline/', views.ClientPaymentTimelineView.as_view(), name='client-payment-timeline'),
    path('clients/early-payments/', views.ClientEarlyPaymentsView.as_view(), name='client-early-payments'),
    path('clients/payment-analytics/', views.client_payment_analytics, name='client-payment-analytics'),

    
   
]