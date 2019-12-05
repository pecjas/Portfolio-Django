from django.contrib import admin
from .models import Project, ProjectImage, Job, JobDetail, Education, Skill

# Register your models here.
admin.site.register(Project)
admin.site.register(ProjectImage)
admin.site.register(Job)
admin.site.register(JobDetail)
admin.site.register(Education)
admin.site.register(Skill)