from django.conf import settings
from django.db import models
from django.urls import reverse
from event_planner.accounts.models import CustomUser


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=255)
    organizer = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        # Redirect to the event detail page after creation
        return reverse('event_detail', kwargs={'pk': self.pk})

    def average_rating(self):
        ratings = self.comments.filter(rating__gt=0).values_list('rating', flat=True)
        return sum(ratings) / len(ratings) if ratings else 0


class Comment(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    rating = models.IntegerField(default=0)  # Rating from 0 to 5
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.event.title}"


class RSVP(models.Model):
    STATUS_CHOICES = [
        ('Going', 'Going'),
        ('Interested', 'Interested'),
        ('Not Going', 'Not Going'),
    ]
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    attendee = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    def __str__(self):
        return f"{self.attendee.username} - {self.event.title} - {self.status}"
