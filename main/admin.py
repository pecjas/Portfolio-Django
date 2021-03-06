from django.contrib import admin
from main.forms import ProjectForm
from .models import Project, ProjectImage, Job, JobDetail, Education, Skill

class ProjectAdmin(admin.ModelAdmin):
    form = ProjectForm
    def save_model(self, request, obj, form, change):
        translation_table = dict.fromkeys(map(ord, "'[]"), None)
        obj.language = obj.language.translate(translation_table)

        super().save_model(request, obj, form, change)

admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectImage)
admin.site.register(Job)
admin.site.register(JobDetail)
admin.site.register(Education)
admin.site.register(Skill)