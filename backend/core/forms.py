from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Insight, Notification

class SignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'email')

class AdminInsightForm(forms.ModelForm):
    class Meta:
        model = Insight
        fields = ['title', 'description', 'category', 'image', 'link']

class MentorInsightForm(forms.ModelForm):
    class Meta:
        model = Insight
        fields = ['title', 'description', 'image', 'link']

class AdminNotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['title', 'content', 'image']