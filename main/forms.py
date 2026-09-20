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
    """Edits Project.language, a comma-joined CharField, as a multi-select.

    The two halves of that translation both live here so they cannot drift:
    string -> list on the way in, list -> string on the way out.
    """

    language = forms.MultipleChoiceField(
        choices=Project.ProgramLanguage.choices,
        widget=forms.SelectMultiple)

    class Meta:
        model = Project
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # MultipleChoiceField marks an option selected when its value appears
        # in the initial iterable. Handed the raw "Python, SQL" string it
        # iterates the characters instead, matches nothing, and every edit
        # opens with an empty selection -- so saving silently dropped whatever
        # the editor did not re-pick.
        current = self.initial.get("language")
        if isinstance(current, str):
            self.initial["language"] = self._split(current)

    def clean_language(self):
        """Back to the storage format, so nothing downstream has to unpick a
        list repr. This replaces the admin's old strip-the-brackets hack."""
        return ", ".join(self.cleaned_data["language"])

    @staticmethod
    def _split(value):
        return [part.strip() for part in value.split(",") if part.strip()]
