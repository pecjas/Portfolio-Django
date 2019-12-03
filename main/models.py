from django.db import models
from django.db.models.query_utils import Q
from django.db.models.signals import post_delete
from django.dispatch import receiver

# Create your models here.
class Project(models.Model):
    title = models.CharField(max_length=200)
    briefDescription = models.CharField(max_length=500)
    content = models.TextField()
    githubLink = models.SlugField(max_length=200, blank=True, null=True)
    webURL = models.SlugField(max_length=200, blank=True, null=True)

    class ProgramLanguage(models.TextChoices):
        Python = 'Python'
        C_Sharp = 'C#'
        SQL = 'SQL'
        PowerShell = 'PowerShell'
        Mumps = 'Mumps'
        Unspecified = 'Unspecified'

    language = models.CharField(choices=ProgramLanguage.choices,
                                default=ProgramLanguage.Unspecified,
                                max_length=50)

    # def __str__(self):
    #     return self.title

class ProjectImage(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='ProjectImage')
    linkedProject = models.ForeignKey(Project, null=True, related_name='images', on_delete=models.SET_NULL)
    mainImage = models.BooleanField(default=False)
        
    class Meta:
        constraints = [
            models.constraints.UniqueConstraint(fields=['linkedProject'],
                                    name='unique_main_image',
                                    condition=Q(mainImage=True))
        ]

    def __str__(self):
        return self.title

@receiver(post_delete, sender=ProjectImage)
def submission_delete(sender, instance, **kwargs):
    instance.image.delete(False)