from django.urls import path
from . import views

urlpatterns = [
    # New APIs
    path('pending-clients/', views.PendingClientsListView.as_view(), name='pending-clients-list'),
    path('client-details/<int:client_id>/', views.ClientContentDetailsView.as_view(), name='client-content-details'),
    path('mark-verified/', views.MarkContentVerifiedView.as_view(), name='mark-content-verified'),
    path('completed-work/', views.CompletedWorkListView.as_view(), name='completed-work-list'),
]
