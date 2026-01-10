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


    #client mark payment url
    
    path('clients/<int:id>/admin-note/', views.ClientAdminNoteView.as_view(), name='client-admin-note'),
    path('clients/<int:id>/admin-note/create/', views.ClientAdminNoteCreateView.as_view(), name='client-admin-note-create'),


    #client process payment url
    path('clients/process-salary-payment/', views.ClientPaymentView.as_view(), name='salary-payment'),
    path('clients/process-salary-payment/<int:id>/', views.ClientPaymentProcessView.as_view(), name='process-salary-payment')
 
]