# tasks/urls.py
from django.urls import path
from . import views

urlpatterns = [
    #create event
    path('event_create/', views.EventCreateView.as_view(), name='event-create'),
    
    #update event
    path('events/<int:id>/update/', views.EventUpdateView.as_view(), name='event-update'),

    #event detail
    path('events/<int:id>/',views.EventDetailView.as_view(),name='event-detail'),

    #event list
    path('events/', views.EventListView.as_view(), name='event-list'),
    
    #delete event
    path('events/<int:id>/delete/', views.EventDeleteView.as_view(), name='event-delete'),

  
]
