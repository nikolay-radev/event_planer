from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import UpdateView, DetailView
from event_planner.accounts.forms import RegisterForm, CustomLoginForm, ProfileForm
from event_planner.accounts.models import Profile

CustomUser = get_user_model()


class CustomRegisterView(View):
    def get(self, request):
        form = RegisterForm()
        return render(request, 'accounts/register.html', {'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Save the new user
            form.save()
            messages.success(request, 'Account created successfully!')
            return redirect('login')
        return render(request, 'accounts/register.html', {'form': form})


class CustomLoginView(LoginView):
    form_class = CustomLoginForm  # Specify the custom form
    template_name = 'accounts/login.html'  # Use your template
    redirect_authenticated_user = True  # Redirect already logged-in users
    next_page = reverse_lazy('event_list')  # Redirect to the event list after login

    def form_valid(self, form):
        """
        Handles successful login.
        Provides a success message when the user logs in with valid credentials.
        """
        messages.success(self.request, f"Login successful! Welcome back, {form.get_user().username}.")
        return super().form_valid(form)

    def form_invalid(self, form):
        """
        Handles failed login attempts.
        Provides an error message for incorrect username or password.
        """
        messages.error(self.request, "Wrong username or password. Please try again.")
        return super().form_invalid(form)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('profile')  # Replace with your profile URL name

    def get_object(self, queryset=None):
        # Ensure the profile being edited belongs to the logged-in user
        return self.request.user.profile

    def get_form_kwargs(self):
        """Pass the logged-in user to the form for email validation."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # Pass the user instance
        return kwargs


class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'accounts/profile_detail.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None):
        # Get the profile by the passed `profile_id`
        return get_object_or_404(Profile, id=self.kwargs['profile_id'])


class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        # Clear all messages on logout
        storage = messages.get_messages(request)
        storage.used = True
        return super().dispatch(request, *args, **kwargs)
