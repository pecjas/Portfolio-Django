from django.shortcuts import get_object_or_404, redirect, render
from django.http import Http404, HttpResponse
from .forms import ContactMeForm
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib import messages
from .models import Project, ProjectImage, Job, JobDetail, Education, Skill
import requests
import json

def index(request):
    # prefetch_related pulls every job's details in one extra query rather than
    # one query per job.
    jobs = Job.objects.order_by('-startDate').prefetch_related('jobdetail_set')

    job_and_detail = {job: list(job.jobdetail_set.all()) for job in jobs}

    return render(
        request,
        "main/home.html",
        context={
            "jobs": job_and_detail,
            "education": Education.objects.all(),
            "skills": Skill.objects.all().order_by('skill'),
            "page_title": "Jason Peck - Software Developer",
            "page_description": "Jason Peck is a software developer working in JavaScript, TypeScript and Python. Read about his professional experience, education and technical skills."})

def portfolio(request):
    main_images = {}

    # select_related avoids a query per image when reading image.linkedProject.
    for image in ProjectImage.objects.filter(mainImage=True).select_related('linkedProject'):
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
            'filterPersonalStatus': filter_personal_status,
            # Display names, as opposed to filterLang's underscored filter keys.
            'languageList': [lang for lang in project.language.split(', ') if lang]
        }})

    language_choices = {}
    for lang in Project.ProgramLanguage.__members__:
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
            'filterList': json.dumps(filter_list_context),
            'page_title': "Portfolio - Jason Peck",
            'page_description': "A selection of professional and personal software projects by Jason Peck, in Python, JavaScript, SQL, PowerShell and more."
        })

def build_portfolio_context(language_choices, personal_choices):
    return {
            'data-filter-personal-status': ' '.join(personal_choices),
            'data-filter-lang': ' '.join([lang for lang in language_choices.keys()])
    }


def project(request, slug):
    project = get_object_or_404(Project, slug=slug)

    template = 'main/project_html.html' if project.html_project else 'main/project_general.html'

    return render(
        request,
        template,
        context={
            "project": project,
            "images": [img for img in ProjectImage.objects.all().filter(linkedProject=project)],
            "page_title": f"{project.title} - Jason Peck",
            "page_description": project.briefDescription})

def legacy_project_redirect(request):
    """Permanently redirects the old /project/?id=<title> URLs to their slug URL."""
    title = request.GET.get('id')

    # Titles are not unique, so match the first rather than risk MultipleObjectsReturned.
    project = Project.objects.filter(title=title).first() if title else None

    if project is None:
        raise Http404("No project matches the requested title.")

    return redirect(project, permanent=True)

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
            "google_recaptcha_site_key": settings.GOOGLE_RECAPTCHA_SITE_KEY,
            "page_title": "Contact - Jason Peck",
            "page_description": "Get in touch with Jason Peck about a project, a role or a question."})

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
