from collections import Counter

from django.db.models import Count, F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.http import Http404, HttpResponse
from .forms import ContactMeForm
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib import messages
from .models import (Education, Job, Project, ProjectImage, Skill,
                     language_project_counts)
import requests
import json

# Display order for the skills section, and the heading each group gets. The
# model's own ordering is alphabetical on the stored value, which would put
# "practice" above "tooling" and capabilities nowhere in particular.
SKILL_GROUPS = [
    (Skill.Category.CAPABILITY, "What I do"),
    (Skill.Category.LANGUAGE, "Languages"),
    (Skill.Category.PLATFORM, "Platforms and frameworks"),
    (Skill.Category.TOOLING, "Tooling"),
    (Skill.Category.PRACTICE, "Ways of working"),
]


def build_skill_groups():
    """Skills grouped by category, each with the evidence behind it.

    A count makes the list an index rather than a claim, so it has to come from
    the same place the portfolio filters read. Capabilities are counted through
    the Skill -> Project relation; languages are counted from Project.language,
    which is what the language filter actually matches on. Counting both from
    the relation would show a number that the link then contradicts.
    """
    # Unpublished projects are not evidence of anything, so they do not count
    # toward a skill either.
    skills = (Skill.objects
              .annotate(project_count=Count(
                  "projects", filter=Q(projects__published=True)))
              .order_by("sort_order", "skill"))

    language_counts = language_project_counts()

    filter_keys = {
        lang.value.casefold(): lang.name
        for lang in Project.ProgramLanguage
    }

    groups = []
    for category, label in SKILL_GROUPS:
        entries = []

        for skill in (s for s in skills if s.category == category):
            count = skill.project_count
            url = ""

            if category == Skill.Category.CAPABILITY and count:
                url = f"{reverse('main:portfolio')}?work={skill.slug}"

            elif category == Skill.Category.LANGUAGE:
                count = language_counts.get(skill.skill.casefold(), 0)
                key = filter_keys.get(skill.skill.casefold())
                if count and key:
                    url = f"{reverse('main:portfolio')}?lang={key}"

            entries.append({"skill": skill.skill, "count": count, "url": url})

        if entries:
            groups.append({"label": label, "skills": entries})

    return groups


def index(request):
    # Bullets live on the job now, so there is no second table to prefetch and
    # no job-to-bullets mapping to build.
    jobs = Job.objects.order_by('-startDate')

    return render(
        request,
        "main/home.html",
        context={
            "jobs": jobs,
            "education": Education.objects.all(),
            "skill_groups": build_skill_groups(),
            "page_title": "Jason Peck - Solution Architect",
            "page_description": "Jason Peck is a Solution Architect working on system integrations, from healthcare interoperability to enterprise process automation, in TypeScript, JavaScript and Python."})

def portfolio(request):
    main_images = {}

    # select_related avoids a query per image when reading image.linkedProject.
    for image in ProjectImage.objects.filter(mainImage=True).select_related('linkedProject'):
        main_images.update({image.linkedProject: image.image.url})

    allProjects = {}

    # Featured first, then anything given a manual order, then most recent,
    # then alphabetical.
    #
    # Both nulls_last matter and they mean different things. On sort_order it
    # keeps the unranked projects below the ranked ones, so a manual number
    # promotes rather than demotes. On startDate it keeps an undated project
    # from outranking a dated one by accident.
    #
    # The manual order is applied across the whole set and the featured split
    # happens afterwards, so a number ranks a project within its own section
    # rather than moving it between sections.
    ordered = (Project.objects
               .filter(published=True)
               .order_by('-featured',
                         F('sort_order').asc(nulls_last=True),
                         F('startDate').desc(nulls_last=True),
                         'title')
               .prefetch_related('skills'))

    # prefetch_related keeps the capability lookup below to one extra query
    # rather than one per project.
    for index, project in enumerate(ordered):
        image = main_images.get(project)

        filter_lang = project.language
        filter_lang = filter_lang.split(', ')
        filter_lang = ' '.join([Project.ProgramLanguage(lang).name for lang in filter_lang])

        capabilities = project.capabilities

        allProjects.update({project: {
            'image': image,
            'filterLang': filter_lang,
            'filterPersonalStatus': project.kind,
            # Display names, as opposed to filterLang's underscored filter keys.
            'languageList': [lang for lang in project.language.split(', ') if lang],
            'filterCapability': ' '.join(c.slug for c in capabilities),
            'capabilityList': capabilities,
            'supportingList': project.supporting_skills,
            # Counted across both sections, so the three images above the fold
            # load eagerly wherever they happen to sit.
            'lazy': index >= 3,
        }})

    language_choices = {}
    for lang in Project.ProgramLanguage.__members__:
        if lang.startswith('_'):
            continue

        language_choices.update({lang: Project.ProgramLanguage[lang]})

    personal_choices = ['Personal', 'Professional']

    # Only capabilities that at least one published project claims. An empty
    # filter option is worse than no option: it advertises a gap rather than
    # hiding it. The count comes from the same pass, so what the menu promises
    # and what the filter returns cannot disagree.
    capability_counts = Counter()
    for details in allProjects.values():
        for capability in details['capabilityList']:
            capability_counts[capability.pk] += 1

    capability_choices = [
        {'skill': skill, 'count': capability_counts[skill.pk]}
        for skill in Skill.objects.filter(category=Skill.Category.CAPABILITY)
        if capability_counts[skill.pk]
    ]

    # Same idea for the language menu, counted off the language strings the
    # filter actually matches on.
    language_counts = Counter()
    for project, details in allProjects.items():
        for name in details['languageList']:
            language_counts[name] += 1

    # Unspecified is the model default rather than a language, so it is not
    # offered as a filter any more than it is rendered on a card.
    language_choices = {
        key: {'label': value, 'count': language_counts[str(value)]}
        for key, value in language_choices.items()
        if key != Project.ProgramLanguage.Unspecified.name
    }

    kind_counts = Counter(project.kind for project in allProjects)

    filter_list_context = build_portfolio_context(
        language_choices, personal_choices, capability_choices)

    personal_choices = [{'label': name, 'count': kind_counts[name]}
                        for name in personal_choices]

    # Rendered as two labelled sections when anything is featured, and as one
    # unlabelled grid when nothing is — which is the pre-Phase-3 page exactly.
    featured_projects = [(p, d) for p, d in allProjects.items() if p.featured]
    other_projects = [(p, d) for p, d in allProjects.items() if not p.featured]

    return render(
        request,
        "main/portfolio.html",
        context={
            'projects': allProjects,
            'featured_projects': featured_projects,
            'other_projects': other_projects,
            'defaultImage': r"main/img/placeholder.png",
            "language_choices": language_choices,
            'data_filter_personal_status': personal_choices,
            'capability_choices': capability_choices,
            'filterList': json.dumps(filter_list_context),
            'page_title': "Portfolio - Jason Peck",
            'page_description': "A selection of professional and personal software projects by Jason Peck, spanning system integration, healthcare interoperability, data pipelines and automation."
        })

def build_portfolio_context(language_choices, personal_choices, capability_choices=()):
    context = {
            'data-filter-personal-status': ' '.join(personal_choices),
            'data-filter-lang': ' '.join([lang for lang in language_choices.keys()])
    }

    if capability_choices:
        context['data-filter-capability'] = ' '.join(
            entry['skill'].slug for entry in capability_choices)

    return context


def project(request, slug):
    project = get_object_or_404(Project, slug=slug)

    return render(
        request,
        'main/project_general.html',
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

def preview_error_page(request, code):
    """Renders 404.html / 500.html at their real status, for development only.

    Django swaps in its own debug 404 whenever DEBUG is True, so the styled
    template is otherwise impossible to look at without turning DEBUG off --
    which also stops runserver serving static files and switches on the HTTPS
    redirect. This route sidesteps both.
    """
    if not settings.DEBUG:
        raise Http404("Error page previews are a development-only route.")

    return render(request, f"{code}.html", status=int(code))


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
