from django import forms
from django.contrib.auth.models import User
from main.models import Project

class ContactMeForm(forms.Form):
    name = forms.CharField(
        max_length=200,
        required="True",
        label="Name",
        widget=forms.TextInput(
            attrs={
                'class': 'dark-purple-border white-text',
                'placeholder': 'Your name'}))

    fromEmail = forms.EmailField(
        required="True",
        label="Email",
        widget=forms.EmailInput(
            attrs={
                'class': 'dark-purple-border white-text',
                'placeholder': 'Your email'}))

    subject = forms.CharField(
        required="True",
        label="Subject",
        widget=forms.TextInput(
            attrs={
                'class': 'dark-purple-border white-text',
                'placeholder': 'Email subject'}))

    message = forms.CharField(
        required="True",
        label="Message",
        widget=forms.Textarea(
            attrs={
                'class': 'dark-purple-border white-text',
                'rows': 10,
                'style': 'height: auto;',
                'placeholder': 'Your message here'}))

class ProjectForm(forms.ModelForm):
    language = forms.MultipleChoiceField(
        choices=Project.ProgramLanguage.choices,
        widget=forms.SelectMultiple)

    class Meta:
        model = Project
        fields = '__all__'
