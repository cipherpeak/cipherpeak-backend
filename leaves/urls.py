from django.urls import path
from . import views

urlpatterns = [
    path('leaves/', views.LeaveListView.as_view(), name='admin-leave-list'),
    path('leaves/<int:pk>/process/', views.LeaveProcessView.as_view(), name='admin-leave-process'),
]
