from django.shortcuts import render
from django.http import HttpResponse
from .forms import ContactMeForm
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib import messages
from .models import Project, ProjectImage, Job, JobDetail, Education, Skill

# Create your views here.
def index(request):
    jobAndDetail = {}
    for job in Job.objects.all():
        jobAndDetail.update({job: [detail for detail in JobDetail.objects.all().filter(relatedJob=job)]})
    return render(request,
                    "main/home.html",
                    context={"jobs": jobAndDetail,
                    "education": Education.objects.all(),
                    "skills": Skill.objects.all().order_by('skill')})

def portfolio(request):
    mainImages = {}
    for image in ProjectImage.objects.all().filter(mainImage=True):
        mainImages.update({image.linkedProject: image.image.url})
    allProjects = {}
    for project in Project.objects.all():
        image = mainImages.get(project)
        allProjects.update({project: image})
    return render(request,
                    "main/portfolio.html",
                    context={"projects": allProjects,
                            "defaultImage": r"main/img/placeholder.png"})

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

def project(request):
    reqID = request.GET.get('id')
    proj = Project.objects.all().filter(title=reqID).first()
    return render(request,
            'main/project.html',
            context={"project": proj,
                    "images": [img for img in ProjectImage.objects.all().filter(linkedProject=proj)]})