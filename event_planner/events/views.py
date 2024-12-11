from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView, View, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import RSVP, Rating
from .forms import EventForm, CommentForm, RatingForm
from django.db.models import Q, Count
from django.views.generic import ListView
from .models import Event


class EventListView(ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 5  # Limit to 10 events per page
    ordering = ['-date', '-time']

    def get_queryset(self):
        """Customize the queryset to handle search functionality."""
        queryset = super().get_queryset()
        query = self.request.GET.get('q')  # Get the search query from the URL
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |  # Search in the title
                Q(description__icontains=query) |  # Search in the description
                Q(location__icontains=query) |  # Search in the location
                Q(category__name__icontains=query)  # Search in the category name
            ).distinct()  # Ensure no duplicate results
        return queryset

    def get_context_data(self, **kwargs):
        """Add the search query to the context for template access."""
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')  # Pass the query to the template
        return context


class EventDetailView(DetailView):
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Fetch RSVP status for the logged-in user
        rsvp_status = "No RSVP yet"
        if self.request.user.is_authenticated:
            rsvp = self.object.rsvp_set.filter(attendee=self.request.user).first()
            if rsvp:
                rsvp_status = rsvp.status

        # Add RSVP counts
        rsvp_counts = self.object.rsvp_set.values('status').annotate(count=Count('status'))

        # Add context for comments, average rating, RSVP counts, and forms
        context['rsvp_status'] = rsvp_status
        context['rsvp_counts'] = rsvp_counts
        context['comments'] = self.object.comments.all()
        context['average_rating'] = self.object.average_rating()
        context['comment_form'] = CommentForm()  # Comment form
        context['rating_form'] = RatingForm()  # Rating form

        return context

    def post(self, request, *args, **kwargs):
        event = self.get_object()  # Get the event object
        user = request.user

        # Ensure the user is authenticated
        if not user.is_authenticated:
            messages.error(request, "You need to log in to perform this action.")
            return redirect('login')

        # Handle RSVP submission
        if 'rsvp_status' in request.POST:
            rsvp_status = request.POST.get('rsvp_status')  # Get the RSVP status from the form
            try:
                # Check if an RSVP already exists for this event and user
                rsvp = event.rsvp_set.filter(attendee=user).first()

                if rsvp:
                    # Update the existing RSVP status
                    rsvp.status = rsvp_status
                    rsvp.save()
                    messages.success(request, "Your RSVP status has been updated successfully!")
                else:
                    # Create a new RSVP if it doesn't exist
                    event.rsvp_set.create(attendee=user, status=rsvp_status)
                    messages.success(request, "Your RSVP status has been submitted successfully!")
            except Exception as e:
                messages.error(request, f"An error occurred while updating your RSVP: {str(e)}")

            return redirect('event_detail', pk=event.pk)

        # Handle rating submission
        if 'value' in request.POST:
            rating_form = RatingForm(request.POST)
            if rating_form.is_valid():
                try:
                    # Check if a rating already exists for this event and user
                    rating = Rating.objects.filter(event=event, user=user).first()

                    if rating:
                        # Update the existing rating
                        rating.value = rating_form.cleaned_data['value']
                        rating.save()
                        messages.success(request, "Your rating has been updated successfully!")
                    else:
                        # Create a new rating if it doesn't exist
                        Rating.objects.create(
                            event=event,
                            user=user,
                            value=rating_form.cleaned_data['value']
                        )
                        messages.success(request, "Your rating has been submitted successfully!")
                except Exception as e:
                    messages.error(request, f"An error occurred while processing your rating: {str(e)}")

            return redirect('event_detail', pk=event.pk)

        # Handle comment submission
        if 'content' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.event = event
                comment.user = user
                comment.save()
                messages.success(request, "Comment added successfully!")
                return redirect('event_detail', pk=event.pk)

        # Default redirection
        return redirect('event_detail', pk=event.pk)


@method_decorator(login_required, name='dispatch')
class EventCreateView(CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/create_event.html'

    def form_valid(self, form):
        form.instance.organizer = self.request.user
        return super().form_valid(form)


class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'events/create_event.html'  # Use the same form template as EventCreateView

    def test_func(self):
        """Ensure that only the event creator can update the event."""
        event = self.get_object()
        return self.request.user == event.organizer

    def handle_no_permission(self):
        """Customize the behavior for unauthorized access."""
        messages.error(self.request, "You do not have permission to edit this event.")
        return super().handle_no_permission()

    def form_valid(self, form):
        """Add a success message upon successful update."""
        messages.success(self.request, "Event updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to the event detail page after updating."""
        return reverse('event_detail', kwargs={'pk': self.object.pk})


class EventDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Event
    template_name = 'events/event_confirm_delete.html'  # Create this template
    success_url = reverse_lazy('event_list')

    def test_func(self):
        """Ensure that only the event creator can delete the event."""
        event = self.get_object()
        return self.request.user == event.organizer

    def handle_no_permission(self):
        """Customize the behavior for unauthorized access."""
        messages.error(self.request, "You do not have permission to delete this event.")
        return super().handle_no_permission()

    def delete(self, request, *args, **kwargs):
        """Add a success message upon successful deletion."""
        messages.success(self.request, "Event deleted successfully!")
        return super().delete(request, *args, **kwargs)


class MyEventListView(LoginRequiredMixin, ListView):
    model = Event
    template_name = 'events/my_event_list.html'  # Create this template
    context_object_name = 'events'

    def get_queryset(self):
        """Filter events to only those created by the logged-in user."""
        return Event.objects.filter(organizer=self.request.user)


class EventSearchView(ListView):
    model = Event
    template_name = 'events/event_search.html'  # Template for search results
    context_object_name = 'events'

    def get_queryset(self):
        query = self.request.GET.get('q', '')  # Get the search query from the URL
        if query:
            return Event.objects.filter(
                Q(title__icontains=query) |  # Search by title
                Q(location__icontains=query) |  # Search by location
                Q(category__name__icontains=query)  # Search by category name
            ).distinct()
        return Event.objects.all()


class EventRSVPView(View):
    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)

        # Check if the user is authenticated
        if request.user.is_authenticated:
            status = request.POST.get('status')

            # Check if the user already has an RSVP
            rsvp = event.rsvp_set.filter(attendee=request.user).first()

            if rsvp:
                # Update the existing RSVP status
                rsvp.status = status
                rsvp.save()
            else:
                # Create a new RSVP if none exists
                RSVP.objects.create(event=event, attendee=request.user, status=status)

            return redirect('event_detail', pk=event.id)
        else:
            return redirect('login')


class MyEventsView(LoginRequiredMixin, TemplateView):
    template_name = 'events/my_events.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Fetch events organized by the logged-in user
        organized_events = Event.objects.filter(organizer=self.request.user)
        organized_paginator = Paginator(organized_events, 5)  # Paginate with 5 events per page
        organized_page_number = self.request.GET.get('organized_page')
        context['organized_events'] = organized_paginator.get_page(organized_page_number)

        # Fetch events the user participates in
        participating_events = Event.objects.filter(rsvp__attendee=self.request.user).distinct()
        participating_paginator = Paginator(participating_events, 5)  # Paginate with 5 events per page
        participating_page_number = self.request.GET.get('participating_page')
        context['participating_events'] = participating_paginator.get_page(participating_page_number)

        return context
