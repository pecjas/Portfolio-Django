from django.shortcuts import render
from django.http import HttpResponse
from .forms import ContactMeForm
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib import messages
from .models import Project, ProjectImage, Job, JobDetail, Education, Skill
import requests
import json

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

        filter_lang = project.language
        filter_lang = filter_lang.split(', ')
        filter_lang = ' '.join([Project.ProgramLanguage(lang).name for lang in filter_lang])

        if project.githubLink != None:
            filter_personal_status = 'Personal'
        else:
            filter_personal_status = 'Professional'

        allProjects.update({project: {
            'image': image,
            'filterLang': filter_lang,
            'filterPersonalStatus': filter_personal_status
        }})

    language_choices = {}
    for lang in dir(Project.ProgramLanguage):
        if lang.startswith('_'):
            continue

        language_choices.update({lang: Project.ProgramLanguage[lang]})

    personal_choices = ['Personal', 'Professional']

    filter_list_context = build_portfolio_context(language_choices, personal_choices)


    return render(
        request,
        "main/portfolio.html",
        context={
            'projects': allProjects,
            'defaultImage': r"main/img/placeholder.png",
            "language_choices": language_choices,
            'data_filter_personal_status': personal_choices,
            'filterList': json.dumps(filter_list_context)
        })

def build_portfolio_context(language_choices, personal_choices):
    return {
            'data-filter-personal-status': ' '.join(personal_choices),
            'data-filter-lang': ' '.join([lang for lang in language_choices.keys()])
    }


def project(request):
    request_id = request.GET.get('id')
    project = Project.objects.get(title=request_id)

    if project.html_project:
        return render(
                    request,
                    'main/project_html.html',
                    context={
                        "project": project,
                        "images": [img for img in ProjectImage.objects.all().filter(linkedProject=project)]})

    return render(
        request,
        'main/project_general.html',
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
        messages.error(request, "I'm sorry, but there was an issue communicating with reCAPTCHA. No email was sent.")

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
