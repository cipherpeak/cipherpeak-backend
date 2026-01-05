# tasks/urls.py
from django.urls import path
from . import views

urlpatterns = [
    #create event
    path('events/', views.EventCreateView.as_view(), name='event-create'),
    
    
    #update event
    path('events/<int:id>/update/', views.EventUpdateView.as_view(), name='event-update'),

    #get event
    path('events/<int:id>/',views.EventDetailView.as_view(),name='event-detail'),

    #event list
    path('event_list/', views.EventListView.as_view(), name='event-list'),
    
    path('events/<int:id>/status/', views.EventStatusUpdateView.as_view(), name='event-status-update'),
    path('events/stats/', views.EventStatsView.as_view(), name='event-stats'),
    path('events/my-events/', views.MyEventsView.as_view(), name='my-events'),
    path('events/created-by-me/', views.EventsCreatedByMeView.as_view(), name='events-created-by-me'),
    path('events/employee/<int:employee_id>/', views.EmployeeEventsView.as_view(), name='employee-events'),
    path('events/calendar/', views.CalendarEventsView.as_view(), name='calendar-events'),

    #delete event
    path('events/<int:id>/delete/', views.EventSoftDeleteView.as_view(), name='event-delete'),
]
