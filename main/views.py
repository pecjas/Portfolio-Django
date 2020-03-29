from django.shortcuts import render
from .forms import ContactMeForm
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib import messages
from .models import Project, ProjectImage, Job, JobDetail, Education, Skill
import requests

def index(request):
    job_and_detail = {}

    for job in Job.objects.all():
        job_and_detail.update(
            {job: [detail for detail in JobDetail.objects.all().filter(relatedJob=job)]})

    return render(
        request,
        "main/home.html",
        context={
            "jobs": job_and_detail,
            "education": Education.objects.all(),
            "skills": Skill.objects.all().order_by('skill')})

def portfolio(request):
    main_images = {}

    for image in ProjectImage.objects.all().filter(mainImage=True):
        main_images.update({image.linkedProject: image.image.url})

    allProjects = {}

    for project in Project.objects.all():
        image = main_images.get(project)
        allProjects.update({project: image})

    return render(
        request,
        "main/portfolio.html",
        context={
            "projects": allProjects,
            "defaultImage": r"main/img/placeholder.png"})

def project(request):
    request_id = request.GET.get('id')
    project = Project.objects.all().filter(title=request_id).first()
    return render(
        request,
        'main/project.html',
        context={
            "project": project,
            "images": [img for img in ProjectImage.objects.all().filter(linkedProject=project)]})

def contact(request):
    if request.method == 'POST':
        form = _get_contact_post_form(request)

    else:
        form = ContactMeForm()

    return render(
        request,
        'main/contact.html',
        context={
            'form': form,
            "google_recaptcha_site_key": settings.GOOGLE_RECAPTCHA_SITE_KEY})

def _get_contact_post_form(request):
    form = ContactMeForm(request.POST)

    if form.is_valid():
        form = _contact_post(request, form)
    
    return form

def _contact_post(request, form):
    if is_recaptcha_successful(request):
        if is_email_delivery_successful(request, form):
            form = ContactMeForm()

    else:
        messages.error(request, "I'm sorry, but you have failed the reCAPTCHA verification. No email was sent.")

    return form

def is_recaptcha_successful(request):
    recaptcha_response = request.POST.get('g-recaptcha-response')

    data = {
        'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
        'response': recaptcha_response
    }

    google_response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
    result = google_response.json()

    return result['success']

def is_email_delivery_successful(request, form) -> bool:
    email = get_contact_me_email(form)

    try:
        email.send()
        messages.success(request, "Thank you. I will get back to you shortly.")
        return True

    except:
        messages.error(request, "Oops, something went wrong. Try again or email me directly at pecjas@gmail.com.")
        return False

def get_contact_me_email(form):
    from_email = form.cleaned_data.get('fromEmail')
    message = f"Name: {form.cleaned_data.get('name')}\nEmail: {from_email}\nMessage: {form.cleaned_data.get('message')}"

    return EmailMessage(
        form.cleaned_data.get('subject'),
        message,
        settings.EMAIL_HOST_USER,
        ['pecjas@gmail.com'],
        headers={'Reply-To': from_email})
