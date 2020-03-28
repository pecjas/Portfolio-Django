from django.db import models
from django.db.models.query_utils import Q
from django.db.models.signals import post_delete
from django.dispatch import receiver

class Job(models.Model):
    employer = models.CharField(max_length=200)
    startDate = models.DateField(verbose_name="Start Date")
    endDate = models.DateField(null=True, blank=True, verbose_name="End Date")
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.employer

class JobDetail(models.Model):
    relatedJob = models.ForeignKey(Job, on_delete=models.CASCADE)
    content = models.TextField()

    def __str__(self):
        return f"({self.relatedJob.employer}) {self.content}"

class Education(models.Model):
    graduationDate = models.DateField(verbose_name="Graduation Date")
    school = models.CharField(max_length=200)
    degree = models.CharField(max_length=200)
    GPA = models.DecimalField(max_digits=4, decimal_places=3)
    additionalInfo = models.TextField(verbose_name="Additional Info")

    def __str__(self):
        return self.school

class Skill(models.Model):
    skill = models.CharField(max_length=200)

    def __str__(self):
        return self.skill

class Project(models.Model):
    title = models.CharField(max_length=200)
    briefDescription = models.CharField(max_length=500, verbose_name="Brief Description")
    content = models.TextField()

    githubLink = models.URLField(max_length=200, blank=True, null=True, verbose_name="Github Link")

    demoVideo = models.FileField(
        upload_to="demoVideo",
        verbose_name="Demo Video",
        blank=True,
        null=True)

    class ProgramLanguage(models.TextChoices):
        Python = 'Python'
        C_Sharp = 'C#'
        SQL = 'SQL'
        PowerShell = 'PowerShell'
        Mumps = 'Mumps'
        HTML = "HTML"
        CSS = "CSS"
        Unspecified = 'Unspecified'

    language = models.CharField(default=ProgramLanguage.Unspecified,
                                max_length=50)

    def __str__(self):
        return self.title

class ProjectImage(models.Model):
    title = models.CharField(max_length=200)

    height = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(default=0)

    image = models.ImageField(upload_to='ProjectImage', height_field='height', width_field='width')
    mainImage = models.BooleanField(default=False, verbose_name="Main Image")

    linkedProject = models.ForeignKey(Project, null=True, related_name='images', on_delete=models.SET_NULL)

    class Meta:
        constraints = [
            models.constraints.UniqueConstraint(
                fields=['linkedProject'],
                name='unique_main_image',
                condition=Q(mainImage=True))
        ]

    def __str__(self):
        return f"({self.linkedProject}) {self.title}"

@receiver(post_delete, sender=ProjectImage)
@receiver(post_delete, sender=Project)
def submission_delete(sender, instance, **kwargs):
    if sender == ProjectImage:
        instance.image.delete(False)

    elif sender == Project:
        instance.demoVideo.delete(False)
