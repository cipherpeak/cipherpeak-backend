# tasks/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('events/', views.EventListCreateView.as_view(), name='event-list-create'),
    path('events/<int:id>/', views.EventDetailView.as_view(), name='event-detail'),
    path('events/<int:id>/status/', views.EventStatusUpdateView.as_view(), name='event-status-update'),
    path('events/stats/', views.EventStatsView.as_view(), name='event-stats'),
    path('events/my-events/', views.MyEventsView.as_view(), name='my-events'),
    path('events/created-by-me/', views.EventsCreatedByMeView.as_view(), name='events-created-by-me'),
    path('events/employee/<int:employee_id>/', views.EmployeeEventsView.as_view(), name='employee-events'),
    path('events/calendar/', views.CalendarEventsView.as_view(), name='calendar-events'),
]
