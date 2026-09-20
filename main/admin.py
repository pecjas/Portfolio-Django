from django import forms
from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.utils.html import format_html

from django.db.models import Count, Q

from main.forms import ProjectForm
from .models import (Education, Job, Project, ProjectImage, Skill,
                     language_project_counts)


class ProjectAdmin(admin.ModelAdmin):
    form = ProjectForm
    prepopulated_fields = {"slug": ("title",)}
    list_display = ("title", "published", "featured", "sort_order", "is_personal",
                    "capability_list", "language", "startDate", "has_outcome")
    list_filter = ("published", "featured", "is_personal", "is_ongoing_program",
                   "skills__category", "skills")
    # Reordering means comparing projects against each other, which is what the
    # changelist is for -- editing them one form at a time is the wrong shape
    # for the job.
    list_editable = ("published", "featured", "sort_order", "is_personal")
    search_fields = ("title", "briefDescription", "outcome")
    filter_horizontal = ("skills",)
    date_hierarchy = "startDate"

    fieldsets = (
        (None, {
            "fields": ("title", "slug", "briefDescription", "outcome", "content")}),
        ("Classification", {
            "fields": ("skills", "language", "is_personal", "featured",
                       "sort_order", "published"),
            "description": "Capabilities drive the portfolio filter. Languages are "
                           "set separately below and are not repeated here. Manual "
                           "order is quicker to set from the project list, where "
                           "you can see what you are ordering against."}),
        ("Dates", {
            "fields": ("startDate", "endDate", "is_ongoing_program"),
            "description": "Optional. Projects with dates sort newest first. Tick "
                           "the programme box for work that runs continuously "
                           "rather than finishing, so it reads as ongoing rather "
                           "than unfinished."}),
        ("Links and media", {
            "fields": ("githubLink", "demoVideo")}),
    )

    def get_queryset(self, request):
        # capability_list reads skills for every row; without this the changelist
        # runs a query per project.
        return super().get_queryset(request).prefetch_related("skills")

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Keeps languages out of the skills picker.

        Languages are stored on Project.language and rendered from it; a
        language attached through this relation is read by nothing --
        `capabilities` filters to capability rows and `supporting_skills`
        excludes languages outright. Offering them here only invited picking
        the same language twice, once to no effect.
        """
        if db_field.name == "skills":
            # order_by overrides Skill.Meta.ordering, which groups by category
            # and then by sort_order -- useful on the page, but it reads as no
            # order at all in a picker you are scanning for one name.
            kwargs["queryset"] = Skill.objects.exclude(
                category=Skill.Category.LANGUAGE).order_by("skill")

        return super().formfield_for_manytomany(db_field, request, **kwargs)

    @admin.display(description="Capabilities")
    def capability_list(self, obj):
        names = [s.skill for s in obj.skills.all() if s.category == Skill.Category.CAPABILITY]
        return ", ".join(names) or "—"

    @admin.display(description="Outcome", boolean=True)
    def has_outcome(self, obj):
        """A column rather than the text: the useful signal is which projects
        are still missing the line that makes them land."""
        return bool(obj.outcome)


class SkillMergeForm(forms.Form):
    """Picks the row the selected skills fold into."""

    target = forms.ModelChoiceField(
        queryset=Skill.objects.none(),
        label="Merge into",
        help_text="Every project tagged with the other selected skills is "
                  "re-tagged to this one, and those skills are then deleted.")


def render_evidence_count(obj, language_counts, tagged_count=None):
    """The count column, and the warning when it is zero.

    One implementation behind two entry points: the `list_display` method,
    which Django's system checks require to exist, and the closure built in
    `get_list_display`, which hoists the language lookup out of the row loop.
    """
    if obj.category == Skill.Category.LANGUAGE:
        # Languages live in Project.language, not the skills relation, so
        # counting them through `Skill.projects` returned zero for every one --
        # JavaScript read 0 while ten projects used it.
        count = language_counts.get(obj.skill.casefold(), 0)
    elif tagged_count is not None:
        count = tagged_count
    else:
        count = obj.projects.filter(published=True).count()

    if count:
        return count

    return format_html(
        '<span style="color:#b3261e;font-weight:600" title="{}">&#9888; 0</span>',
        "No published project demonstrates this skill, so it renders on the "
        "home page as a claim with no evidence behind it.")


class SkillAdmin(admin.ModelAdmin):
    list_display = ("skill", "category", "sort_order", "project_count")
    list_editable = ("category", "sort_order")
    list_filter = ("category",)
    search_fields = ("skill",)
    prepopulated_fields = {"slug": ("skill",)}
    ordering = ("category", "sort_order", "skill")
    actions = ["merge_skills"]

    def get_queryset(self, request):
        # Unpublished projects are not evidence, so they do not count.
        return (super().get_queryset(request)
                .prefetch_related("projects")
                .annotate(tagged_count=Count(
                    "projects", filter=Q(projects__published=True))))

    @admin.display(description="Projects")
    def project_count(self, obj):
        return render_evidence_count(obj, language_project_counts(),
                                     getattr(obj, "tagged_count", None))

    def get_list_display(self, request):
        """Same column, with the language map read once per page rather than
        once per row."""
        language_counts = language_project_counts()

        def project_count(obj):
            return render_evidence_count(obj, language_counts,
                                         getattr(obj, "tagged_count", None))

        project_count.short_description = "Projects"

        return ("skill", "category", "sort_order", project_count)

    @admin.action(description="Merge selected skills into one")
    def merge_skills(self, request, queryset):
        """Re-tags every project and deletes the leftovers.

        Taxonomy changes otherwise need a migration each time. This keeps them in
        the admin, where the person who knows the content is already working.
        """
        if request.POST.get("merge_confirmed"):
            form = SkillMergeForm(request.POST)
            form.fields["target"].queryset = queryset

            if form.is_valid():
                target = form.cleaned_data["target"]
                sources = [s for s in queryset if s.pk != target.pk]

                moved = 0
                for skill in sources:
                    for project in skill.projects.all():
                        project.skills.add(target)
                        project.skills.remove(skill)
                        moved += 1
                    skill.delete()

                self.message_user(
                    request,
                    f'Merged {len(sources)} skill(s) into "{target.skill}", '
                    f"re-tagging {moved} project link(s).",
                    messages.SUCCESS)
                return redirect(request.get_full_path())
        else:
            form = SkillMergeForm(initial={"target": queryset.first()})
            form.fields["target"].queryset = queryset

        return render(request, "admin/main/skill/merge.html", {
            "title": "Merge skills",
            "skills": queryset,
            "form": form,
            "action_checkbox_name": admin.helpers.ACTION_CHECKBOX_NAME,
            "opts": self.model._meta,
        })


class JobAdmin(admin.ModelAdmin):
    """Positions, grouped by employer.

    The changelist fell back to __str__, which was the company name, so the
    four levels at Esker rendered as four identical rows. Title leads, and
    rows sort by employer and then newest first, which puts the levels held at
    one company together and in the order they were held.
    """

    list_display = ("title", "employer", "startDate", "end_date", "bullet_count")
    list_filter = ("employer",)
    search_fields = ("title", "employer", "responsibilities")
    ordering = ("employer", "-startDate")

    fieldsets = (
        (None, {"fields": ("title", "employer")}),
        ("Dates", {"fields": ("startDate", "endDate"),
                   "description": "Leave the end date blank for the role you "
                                  "currently hold."}),
        ("Responsibilities", {
            "fields": ("responsibilities",),
            "description": "One bullet per line, in the order they should "
                           "appear on the page. Reorder by moving the lines."}),
    )

    @admin.display(description="End Date", ordering="endDate")
    def end_date(self, obj):
        # A blank endDate means the role is current -- the same thing the
        # Experience section renders as "Present". An empty cell reads as
        # missing data instead.
        return obj.endDate or "Present"

    @admin.display(description="Bullets")
    def bullet_count(self, obj):
        """Counts what the page will actually render, blank lines excluded, so
        a stray newline does not read as a bullet here and vanish there."""
        return len(obj.responsibility_lines)


class EducationAdmin(admin.ModelAdmin):
    list_display = ("degree", "school", "credential_type", "graduationDate", "GPA")
    list_filter = ("credential_type",)
    list_editable = ("credential_type",)
    ordering = ("-graduationDate",)


admin.site.register(Project, ProjectAdmin)
admin.site.register(Skill, SkillAdmin)
admin.site.register(ProjectImage)
admin.site.register(Job, JobAdmin)
admin.site.register(Education, EducationAdmin)
