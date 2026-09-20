"""Seeds the capability vocabulary and sorts existing skills into categories.

Creating the capability rows here rather than leaving them to be typed in the
admin keeps the vocabulary small and consistent — the whole point of the axis
is that six values mean something and twenty do not.

Existing skills are categorised by name. Anything unrecognised is left at the
model default (`language`) rather than guessed at, so a wrong category is a
visible, one-click fix rather than a silent mislabelling.
"""
from django.db import migrations
from django.utils.text import slugify

# Duplicated from 0004 rather than imported: migration modules start with a
# digit and are not importable, and a historical migration should not depend on
# current model code anyway.
SLUG_SUBSTITUTIONS = (("++", " plus plus"), ("#", " sharp"), ("&", " and "))


def _slug_source(text):
    for symbol, words in SLUG_SUBSTITUTIONS:
        text = text.replace(symbol, words)

    return text

# The primary portfolio axis. Order is the display order.
CAPABILITIES = [
    ("Systems Integration", 10),
    ("Healthcare Interoperability", 20),
    ("Data & ETL", 30),
    ("Automation & Tooling", 40),
    ("Compliance & Process", 50),
    ("Web Applications", 60),
]

# Existing skills, by name, to their category. Names are matched case-insensitively.
RECATEGORISE = {
    "language": [
        "C#", "Java", "JavaScript", "TypeScript", "M (Mumps)", "Mumps",
        "PowerShell", "Python", "SQL", "HTML", "CSS", "PHP",
    ],
    "platform": ["Django", "Esker", "Epic"],
    "tooling": ["AI", "ChatGPT", "Claude", "Claude Code", "LLM", "Copilot",
                "Microsoft Copilot"],
    "practice": ["Communication", "Critical Thinking", "Teaching",
                 "Mathematics", "Scrum", "Technical Leadership"],
}


def unique_slug(base, taken):
    slug = base or "skill"
    suffix = 2
    while slug in taken:
        slug = f"{base}-{suffix}"
        suffix += 1

    taken.add(slug)
    return slug


def seed(apps, schema_editor):
    Skill = apps.get_model("main", "Skill")

    lookup = {}
    for category, names in RECATEGORISE.items():
        for name in names:
            lookup[name.casefold()] = category

    taken = set(Skill.objects.exclude(slug="").values_list("slug", flat=True))

    for skill in Skill.objects.all():
        category = lookup.get(skill.skill.strip().casefold())
        if category and skill.category != category:
            skill.category = category
            skill.save(update_fields=["category"])

    for name, order in CAPABILITIES:
        if Skill.objects.filter(skill__iexact=name).exists():
            continue

        Skill.objects.create(
            skill=name,
            category="capability",
            sort_order=order,
            slug=unique_slug(slugify(_slug_source(name)), taken))


def unseed(apps, schema_editor):
    """Removes only the seeded capabilities, and only while nothing uses them.

    A capability a project has been tagged with is content, not scaffolding, so
    rolling this migration back must not silently discard it.
    """
    Skill = apps.get_model("main", "Skill")

    for name, _ in CAPABILITIES:
        seeded = Skill.objects.filter(skill__iexact=name, category="capability")
        seeded = [s for s in seeded if not s.projects.exists()]

        for skill in seeded:
            skill.delete()


class Migration(migrations.Migration):

    dependencies = [("main", "0004_project_capabilities")]

    operations = [migrations.RunPython(seed, unseed)]
