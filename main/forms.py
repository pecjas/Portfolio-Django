from django import forms
#from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class ContactMeForm(forms.Form):
    name = forms.CharField(max_length=200, required="True", label="Your Name")
    fromEmail = forms.EmailField(required="True", label="Your Email")
    subject = forms.CharField(required="True", label="Subject")
    #TODO: Increase size of message TextArea
    message = forms.CharField(widget=forms.Textarea(attrs={'row':5, "cols":50}), required="True", label="Message")

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