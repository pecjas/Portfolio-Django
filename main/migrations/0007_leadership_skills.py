"""Adds Project Management and Leadership as selectable practice skills.

Seeded rather than typed into the admin so dev and production end up with the
same rows without anyone entering them twice.

Category is `practice`, not `capability`: the capability axis answers "what kind
of work is this project" -- Systems Integration, Healthcare Interoperability --
and stays a small fixed set to be worth filtering on. These two answer "how did
he contribute", which is what `practice` is for. They are still selectable per
project and still render on the card.
"""
from django.db import migrations
from django.utils.text import slugify

SKILLS = [
    ("Project Management", 10),
    ("Leadership", 20),
]


def seed(apps, schema_editor):
    Skill = apps.get_model("main", "Skill")

    taken = set(Skill.objects.exclude(slug="").values_list("slug", flat=True))

    for name, order in SKILLS:
        if Skill.objects.filter(skill__iexact=name).exists():
            continue

        slug = slugify(name)
        suffix = 2
        while slug in taken:
            slug = f"{slugify(name)}-{suffix}"
            suffix += 1

        taken.add(slug)
        Skill.objects.create(
            skill=name, category="practice", sort_order=order, slug=slug)


def unseed(apps, schema_editor):
    """Removes them only while no project uses them -- a tagged skill is
    content, and rolling a migration back should not discard content."""
    Skill = apps.get_model("main", "Skill")

    for name, _ in SKILLS:
        for skill in Skill.objects.filter(skill__iexact=name, category="practice"):
            if not skill.projects.exists():
                skill.delete()


class Migration(migrations.Migration):

    dependencies = [("main", "0006_education_credentials")]

    operations = [migrations.RunPython(seed, unseed)]
