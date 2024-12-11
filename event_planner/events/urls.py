from django.urls import path
from . import views
from .views import (
    EventListView,
    EventDetailView,
    EventCreateView,
    EventUpdateView,
    EventDeleteView,
    MyEventListView,
    EventSearchView,
    EventRSVPView,
)

urlpatterns = [
    path('', EventListView.as_view(), name='event_list'),  # View all events
    path('<int:pk>/', EventDetailView.as_view(), name='event_detail'),  # View event details
    path('create/', EventCreateView.as_view(), name='event_create'),  # Create a new event
    path('<int:pk>/update/', EventUpdateView.as_view(), name='event_update'),  # Update an event
    path('<int:pk>/delete/', EventDeleteView.as_view(), name='event_delete'),  # Delete an event
    path('my-events/', MyEventListView.as_view(), name='my_events'),  # List user's events
    path('search/', EventSearchView.as_view(), name='event_search'),  # Search events
    path('<int:pk>/rsvp/', EventRSVPView.as_view(), name='event_rsvp'),  # RSVP for an event
]
