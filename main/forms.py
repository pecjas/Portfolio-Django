from django import forms
#from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from main.models import Project

class ContactMeForm(forms.Form):
    name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'dark-purple-border white-text'}), required="True", label="Your Name")
    fromEmail = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'dark-purple-border white-text'}), required="True", label="Your Email")
    subject = forms.CharField(widget=forms.TextInput(attrs={'class': 'dark-purple-border white-text'}), required="True", label="Subject")
    #TODO: Increase size of message TextArea
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'dark-purple-border white-text'}), required="True", label="Message")

class ProjectForm(forms.ModelForm):
    language = forms.MultipleChoiceField(choices=Project.ProgramLanguage.choices,
                                        widget=forms.SelectMultiple)
    class Meta:
        model = Project
        fields = '__all__'

#region NewUserForm if needed
# class NewUserForm(UserCreationForm):
#     email = forms.EmailField(required=True)

#     class Meta:
#         model = User
#         fields = ("username", "email", "password1", "password2")

#     def save(self, commit=True):
#         user = super(NewUserForm, self).save(commit=False)
#         user.email = self.cleaned_data['email']
#         if commit:
#             user.save()
#         return user
#endregion