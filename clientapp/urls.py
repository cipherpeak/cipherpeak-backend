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

    #client document delete url
    path('client-documents/<int:pk>/delete/', views.ClientDocumentDeleteView.as_view(), name='delete_client_document'),
    
    #client delete url
    path('clients/delete/<int:id>/', views.ClientDeleteView.as_view(), name='delete_client'),


    #client admin note url
    path('clients/<int:id>/admin-note/', views.ClientAdminNoteView.as_view(), name='client-admin-note'),
    path('clients/<int:id>/admin-note/create/', views.ClientAdminNoteCreateView.as_view(), name='client-admin-note-create'),

    # New client payment endpoints
    path('clients/<int:pk>/process-payment/', views.ProcessClientPaymentView.as_view(), name='process-client-payment'),
    path('clients/<int:client_id>/payment-history/', views.ClientPaymentHistoryListView.as_view(), name='client-payment-history'),
    path('clients/<int:id>/payment-detail/', views.ClientPaymentDetailView.as_view(), name='client-payment-detail'),
]