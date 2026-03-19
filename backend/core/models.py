from django.db import models
from django.contrib.auth.models import User
import random

# Anonymous names
ANON_NAMES = [
    "Anonymous Rose 🌸",
    "Anonymous Moon 🌙",
    "Anonymous Sparrow 🕊️",
    "Anonymous Daisy 🌼",
    "Anonymous Star ⭐"
]

def get_random_anon_name():
    return random.choice(ANON_NAMES)

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    anon_name = models.CharField(max_length=50, default=get_random_anon_name)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.anon_name}: {self.content[:20]}"

class Reply(models.Model):
    post = models.ForeignKey(Post, related_name='replies', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    anon_name = models.CharField(max_length=50, default=get_random_anon_name)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Reaction(models.Model):
    post = models.ForeignKey(Post, related_name='reactions', on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Insight(models.Model):
    CATEGORY_CHOICES = [
        ('emotional', 'Emotional Well-being'),
        ('academic', 'Academic Success'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    image = models.CharField(max_length=500, help_text="Path to static image or URL", blank=True, null=True)
    link = models.CharField(max_length=500, default="#")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Notification(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.CharField(max_length=500, help_text="Path to static image or URL", blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_unread = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class MentorProfile(models.Model):
    MENTOR_CHOICES = [
        ('academic', 'Academic Mentor'),
        ('emotional', 'Emotional Mentor'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mentor_type = models.CharField(max_length=20, choices=MENTOR_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.get_mentor_type_display()}"

class MentorMessage(models.Model):
    MENTOR_CHOICES = [
        ('academic', 'Academic Mentor'),
        ('emotional', 'Emotional Mentor'),
    ]
    session_user = models.ForeignKey(User, related_name='mentor_sessions', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='sent_mentor_messages', on_delete=models.CASCADE)
    mentor_type = models.CharField(max_length=20, choices=MENTOR_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.username} to {self.mentor_type} session of {self.session_user.username}"

class Report(models.Model):
    post = models.ForeignKey(Post, related_name='reports', on_delete=models.CASCADE)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report by {self.reporter.username} on Post {self.post.id}"