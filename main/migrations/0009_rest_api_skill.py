"""Adds REST API as a selectable skill.

Category is `platform` rather than `capability`: the capability axis is what a
visitor filters on, and it answers "what kind of work is this" -- Systems
Integration already covers the domain these projects sit in. REST API is the
technology used to do it, so it belongs with the supporting detail that renders
beneath the description, alongside Django.

Seeded rather than typed into the admin so dev and production match without
anyone entering it twice.
"""
from django.db import migrations
from django.utils.text import slugify

NAME = "REST API"
CATEGORY = "platform"
SORT_ORDER = 10


def seed(apps, schema_editor):
    Skill = apps.get_model("main", "Skill")

    if Skill.objects.filter(skill__iexact=NAME).exists():
        return

    taken = set(Skill.objects.exclude(slug="").values_list("slug", flat=True))

    slug = slugify(NAME)
    suffix = 2
    while slug in taken:
        slug = f"{slugify(NAME)}-{suffix}"
        suffix += 1

    Skill.objects.create(
        skill=NAME, category=CATEGORY, sort_order=SORT_ORDER, slug=slug)


def unseed(apps, schema_editor):
    """Only while nothing uses it -- a tagged skill is content, and rolling a
    migration back should not discard content."""
    Skill = apps.get_model("main", "Skill")

    for skill in Skill.objects.filter(skill__iexact=NAME, category=CATEGORY):
        if not skill.projects.exists():
            skill.delete()


class Migration(migrations.Migration):

    dependencies = [("main", "0008_project_default_professional")]

    operations = [migrations.RunPython(seed, unseed)]
