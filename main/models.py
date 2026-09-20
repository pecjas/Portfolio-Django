from django.db import models
from django.db.models.query_utils import Q
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils.text import slugify


# slugify() strips symbols outright, so "C#" becomes "c" and "C++" becomes "c".
# Spelling them first keeps the filter values readable and distinct.
SLUG_SUBSTITUTIONS = (("++", " plus plus"), ("#", " sharp"), ("&", " and "))


def _slug_source(text):
    for symbol, words in SLUG_SUBSTITUTIONS:
        text = text.replace(symbol, words)

    return text


def _build_unique_slug(instance, source, fallback="item"):
    """A slug for `source` that no other row of this model holds.

    Shared by Project and Skill; both need the same collision handling and
    neither should silently overwrite the other's slug.
    """
    base = slugify(_slug_source(source)) or fallback
    slug = base
    suffix = 2

    taken = type(instance).objects.exclude(pk=instance.pk)
    while taken.filter(slug=slug).exists():
        slug = f"{base}-{suffix}"
        suffix += 1

    return slug


class Job(models.Model):
    employer = models.CharField(max_length=200)
    startDate = models.DateField(verbose_name="Start Date")
    endDate = models.DateField(null=True, blank=True, verbose_name="End Date")
    title = models.CharField(max_length=200)

    # Replaces the JobDetail table. A bullet had no identity, no ordering, no
    # fields of its own and nothing pointing at it -- a list of strings stored
    # as rows. Worse, JobDetail declared no ordering and the view never asked
    # for one, so the bullets rendered in whatever order SQLite returned and
    # could not be reordered except by retyping every line below the one being
    # moved. Here the order you type is the order the page renders.
    responsibilities = models.TextField(
        blank=True,
        help_text="One bullet per line. Blank lines are ignored. The order "
                  "you type is the order the page renders.")

    def __str__(self):
        # Several levels have been held at the same employer, so the company
        # name alone does not identify a row -- in the changelist, in the
        # related-job picker, or anywhere else Django falls back to this.
        return f"{self.title} — {self.employer}"

    @property
    def responsibility_lines(self):
        """The bullets, in order, with the blanks dropped.

        splitlines() rather than split("\n") because it treats a lone carriage
        return as a line ending too. The strip() below already absorbs the
        one a browser leaves on the end of each CRLF line, so that case is
        covered either way -- this is the case it is not.
        """
        return [line.strip()
                for line in self.responsibilities.splitlines()
                if line.strip()]


class JobDetail(models.Model):
    """Superseded by Job.responsibilities, and no longer read by anything.

    Migration 0012 copies every row into the new field. The table is kept for
    one release so a rollback has something to roll back to; the migration that
    drops it comes next, once the backfill has been seen to be right in
    production.
    """

    relatedJob = models.ForeignKey(Job, on_delete=models.CASCADE)
    content = models.TextField()

    class Meta:
        # The ordering the backfill assumes, made explicit. It was absent,
        # which is how the bullets came to have no dependable order.
        ordering = ("pk",)

    def __str__(self):
        return f"({self.relatedJob.employer}) {self.content}"

class Education(models.Model):
    """A credential: a degree, or a certificate that has no GPA to report."""

    class Credential(models.TextChoices):
        DEGREE = "degree", "Degree"
        CERTIFICATE = "certificate", "Certificate"

    credential_type = models.CharField(
        max_length=20,
        choices=Credential.choices,
        default=Credential.DEGREE,
        verbose_name="Credential type")

    graduationDate = models.DateField(verbose_name="Completion Date")
    school = models.CharField(max_length=200)
    degree = models.CharField(max_length=200, verbose_name="Credential")

    # Optional, because a certificate has no GPA -- and because a GPA earned
    # years ago is worth less than the space it takes on the page.
    GPA = models.DecimalField(
        max_digits=4, decimal_places=3, null=True, blank=True,
        verbose_name="GPA",
        help_text="Leave blank to omit it from the page.")

    additionalInfo = models.TextField(
        verbose_name="Additional Info", blank=True)

    class Meta:
        # Most recent credential first, so the newest thing earned leads.
        ordering = ("-graduationDate",)

    def __str__(self):
        return f"{self.degree} ({self.school})"

    @property
    def is_certificate(self):
        return self.credential_type == self.Credential.CERTIFICATE

class Skill(models.Model):
    """A capability, language, platform, tool or practice.

    Categorised because the flat alphabetical list put "Critical Thinking"
    beside "C#", which told a reader nothing about depth. The `capability`
    rows additionally drive the portfolio page's primary filter, so a skill and
    the projects proving it are the same object rather than two unconnected
    lists.
    """

    class Category(models.TextChoices):
        CAPABILITY = "capability", "Capability"
        LANGUAGE = "language", "Language"
        PLATFORM = "platform", "Framework or platform"
        TOOLING = "tooling", "Tooling"
        PRACTICE = "practice", "Ways of working"

    skill = models.CharField(max_length=200)

    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.LANGUAGE,
        help_text="Only capabilities drive the portfolio filter.")

    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True,
        help_text="Used as the filter value and in portfolio URLs. Generated from the name.")

    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Lower sorts first within a category. Ties fall back to the name.")

    class Meta:
        ordering = ("category", "sort_order", "skill")

    def __str__(self):
        return self.skill

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _build_unique_slug(self, self.skill, "skill")

        super().save(*args, **kwargs)

    @property
    def is_capability(self):
        return self.category == self.Category.CAPABILITY

class Project(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    briefDescription = models.CharField(max_length=500, verbose_name="Brief Description")
    content = models.TextField()

    githubLink = models.URLField(max_length=200, blank=True, null=True, verbose_name="Github Link")

    # Whether a project is personal used to be inferred from githubLink being
    # set, which conflated two unrelated facts: a professional project can have
    # public source, and a personal one need not.
    is_personal = models.BooleanField(
        default=False,
        verbose_name="Personal project",
        help_text="Personal projects are shown in the accent colour; professional ones in purple.")

    demoVideo = models.FileField(
        upload_to="demoVideo",
        verbose_name="Demo Video",
        blank=True,
        null=True)

    class ProgramLanguage(models.TextChoices):
        C_Sharp = 'C#'
        CSS = "CSS"
        HTML = "HTML"
        JavaScript = 'JavaScript'
        Mumps = 'Mumps'
        PHP = 'PHP'
        PowerShell = 'PowerShell'
        Python = 'Python'
        SQL = 'SQL'
        TypeScript = 'TypeScript'
        Unspecified = 'Unspecified'

    language = models.CharField(default=ProgramLanguage.Unspecified,
                                max_length=200)

    # What kind of work this was, as opposed to what it was written in. This is
    # the axis a hiring manager actually screens on; language is a detail.
    skills = models.ManyToManyField(
        "Skill",
        blank=True,
        related_name="projects",
        verbose_name="Capabilities and tools",
        help_text="Capabilities drive the portfolio filter. Platforms and tooling show as tags.")

    featured = models.BooleanField(
        default=False,
        help_text="Featured projects lead the portfolio page under 'Featured work'.")

    # Nullable rather than a default of 0, because "no opinion" and "first"
    # have to be different answers. A default would silently pin every project
    # to the same rank and leave the real ordering to the tiebreakers.
    sort_order = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Manual order",
        help_text="Leave blank for the default order, newest first. Give a "
                  "number to pin a project to the top of its section: 1 before "
                  "2 before 3, and everything numbered sits above everything "
                  "blank. Featured projects are still ordered separately from "
                  "the rest.")

    published = models.BooleanField(
        default=True,
        help_text="Unpublished projects stay in the admin and never reach the site.")

    outcome = models.CharField(
        max_length=300,
        blank=True,
        help_text="One line on what the work was worth — time saved, volume "
                  "handled, what it replaced. Renders above the description, and "
                  "is skipped entirely while blank.")

    is_ongoing_program = models.BooleanField(
        default=False,
        verbose_name="Ongoing programme of work",
        help_text="For work that runs continuously rather than finishing. Reads "
                  "as 'Ongoing since ...' instead of '... – Present'.")

    startDate = models.DateField(
        null=True, blank=True, verbose_name="Start Date",
        help_text="Optional. Used to order projects and to show when the work happened.")

    endDate = models.DateField(
        null=True, blank=True, verbose_name="End Date",
        help_text="Leave blank for ongoing work.")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _build_unique_slug(self, self.title, "project")

        super().save(*args, **kwargs)

    @property
    def kind(self):
        return "Personal" if self.is_personal else "Professional"

    @property
    def date_range(self):
        """"Mar 2024 - Aug 2024", or "" when neither date is set.

        An open end date means ongoing, matching how the Experience section
        already reads a null Job.endDate. Empty string rather than None so a
        template can test it directly.
        """
        if not self.startDate and not self.endDate:
            return ""

        def month(value):
            return value.strftime("%b %Y")

        if self.startDate and self.endDate:
            if month(self.startDate) == month(self.endDate):
                return month(self.startDate)

            return f"{month(self.startDate)} – {month(self.endDate)}"

        if self.startDate:
            # Six simultaneous "Present" entries read as though nothing ever
            # finishes; "Ongoing since" reads as sustained ownership.
            if self.is_ongoing_program:
                return f"Ongoing since {month(self.startDate)}"

            return f"{month(self.startDate)} – Present"

        return month(self.endDate)

    @property
    def capabilities(self):
        """Capability skills only. Empty until content is assigned, which every
        template that uses it has to tolerate."""
        return [s for s in self.skills.all() if s.is_capability]

    @property
    def supporting_skills(self):
        """Platforms, tooling and practices — everything but capabilities and
        languages, which are rendered from their own fields."""
        excluded = {Skill.Category.CAPABILITY, Skill.Category.LANGUAGE}
        return [s for s in self.skills.all() if s.category not in excluded]

    def get_absolute_url(self):
        return reverse("main:project", kwargs={"slug": self.slug})

    def __str__(self):
        return self.title

def language_project_counts(projects=None):
    """How many projects list each language, keyed casefolded.

    Languages are stored in Project.language as a comma-joined string, not in
    the skills relation, so counting a language Skill through `Skill.projects`
    returns zero for every one of them. Anything reporting language usage has
    to read it from here instead.

    Published projects only, so the number matches what the site shows.
    """
    if projects is None:
        projects = Project.objects.filter(published=True)

    unspecified = Project.ProgramLanguage.Unspecified.value
    counts = {}

    for raw in projects.values_list("language", flat=True):
        for part in (raw or "").split(","):
            name = part.strip()
            if name and name != unspecified:
                counts[name.casefold()] = counts.get(name.casefold(), 0) + 1

    return counts


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
