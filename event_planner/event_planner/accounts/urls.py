from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views
from .views import ProfileUpdateView, ProfileDetailView, CustomLogoutView

urlpatterns = [
    path('register/', views.CustomRegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('profile/', ProfileUpdateView.as_view(), name='profile'),
    path('profile/<int:profile_id>/', ProfileDetailView.as_view(), name='profile_detail')
]
