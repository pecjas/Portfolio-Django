from django.shortcuts import render
from django.http import HttpResponse
from .forms import ContactMeForm
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib import messages

# Create your views here.
def index(request):
    return render(request,
                    "main/home.html",
                    context=None)

def portfolio(request):
    return render(request,
                    "main/portfolio.html",
                    context=None)

def contact(request):
    if request.method == 'POST':
        form = ContactMeForm(request.POST)
        if form.is_valid():
            fromEmail = form.cleaned_data.get('fromEmail')
            message = f"Name: {form.cleaned_data.get('name')}\nEmail: {fromEmail}\nMessage: {form.cleaned_data.get('message')}"
            email = EmailMessage(form.cleaned_data.get('subject'),
                                message,
                                settings.EMAIL_HOST_USER,
                                ['pecjas@gmail.com'],
                                headers = {'Reply-To': fromEmail}   )
            try:
                email.send()
                messages.success(request, "Thank you. I will get back to you shortly.")
                form = ContactMeForm()
            except:
                messages.error(request, "Oops, something went wrong. Try again or email me directly at pecjas@gmail.com.")
            #TODO: Use Toast instead of HttpResponse
    else:
        form = ContactMeForm()
    return render(request, 
                'main/contact.html', 
                {'form': form})