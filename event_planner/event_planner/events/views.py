from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import RSVP
from .forms import EventForm, CommentForm
from django.db.models import Q
from django.views.generic import ListView
from .models import Event


class EventListView(ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 10  # Limit to 10 events per page

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

        # Add RSVP status and comments to the context
        context['rsvp_status'] = rsvp_status
        context['comments'] = self.object.comments.all()
        context['average_rating'] = self.object.average_rating()
        context['form'] = CommentForm()  # Add the comment form to the context

        return context

    def post(self, request, *args, **kwargs):
        event = self.get_object()  # Get the event object

        # Check if the submission is for comments
        if 'content' in request.POST and 'rating' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.event = event
                comment.user = request.user
                comment.save()
                return redirect('event_detail', pk=event.pk)

        # Otherwise, handle RSVP submission
        if not request.user.is_authenticated:
            return redirect('login')

        rsvp, created = RSVP.objects.get_or_create(event=event, attendee=request.user)
        new_status = request.POST.get('status')

        if new_status not in dict(RSVP.STATUS_CHOICES):
            return HttpResponseForbidden("Invalid RSVP status.")

        rsvp.status = new_status
        rsvp.save()
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
