from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('event_planner.events.urls')),  # Your events URLs
    path('accounts/', include('event_planner.accounts.urls')),  # Authentication URLs
]
