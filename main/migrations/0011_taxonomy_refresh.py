"""Sharpens the capability axis and tidies the AI skills.

Three changes, all driven by the review in PROJECT-REVIEW.md:

1. "Automation & Tooling" had spread to 11 of 18 projects, so it no longer
   narrowed anything. The AI work is split out as its own capability, which
   drops Automation & Tooling to a meaningful count and puts the most current,
   most differentiating work on the axis recruiters scan first.

2. "Web Applications" is renamed to "SaaS Platform Development". It was tagged
   on account consolidation, e-invoicing and ISO 27001 -- none of which is a
   web application in the sense a reader takes it. They are customisations on a
   SaaS platform, which is the actual job.

3. AI, ChatGPT, Claude and LLM co-occurred on every AI project, rendering four
   pills that said one thing. They collapse to named tools plus LLM.

Matching is by slug and by case-insensitive name, and every step is skipped
when its target is missing, so this is safe to run against a database that has
already been edited by hand.
"""
from django.db import migrations
from django.utils.text import slugify

AI_CAPABILITY = "AI & LLM Solutions"
AI_CAPABILITY_SLUG = "ai-and-llm-solutions"

# Projects whose work is genuinely AI-led. Each gains the new capability; the
# first three lose Automation & Tooling because AI is the better description.
AI_PROJECTS = {
    "ai-tooling": {"drop_automation": True},
    "llm-order-extraction": {"drop_automation": True},
    "configurable-edi-850-integration-framework": {"drop_automation": False},
    "erp-integrations": {"drop_automation": False},
}

RENAMES = [
    ("Web Applications", "SaaS Platform Development", "saas-platform-development"),
    ("Claude", "Claude Code", "claude-code"),
]

# Retired in favour of the capability and the named tools above.
RETIRE = ["AI"]

# Seeded unconditionally, so the tool vocabulary is the same in a fresh
# database as in one carrying production data. Existing rows are left alone.
ADD_TOOLS = [
    ("Claude Code", "tooling", 10),
    ("Microsoft Copilot", "tooling", 20),
    ("ChatGPT", "tooling", 30),
    ("LLM", "tooling", 40),
]


def unique_slug(Skill, base):
    slug, suffix = base, 2
    while Skill.objects.filter(slug=slug).exists():
        slug = f"{base}-{suffix}"
        suffix += 1
    return slug


def forwards(apps, schema_editor):
    Skill = apps.get_model("main", "Skill")
    Project = apps.get_model("main", "Project")

    # --- 1. the new capability ---------------------------------------------
    capability = Skill.objects.filter(skill__iexact=AI_CAPABILITY).first()
    if capability is None:
        capability = Skill.objects.create(
            skill=AI_CAPABILITY, category="capability", sort_order=35,
            slug=unique_slug(Skill, AI_CAPABILITY_SLUG))

    automation = Skill.objects.filter(skill__iexact="Automation & Tooling").first()

    for slug, options in AI_PROJECTS.items():
        project = Project.objects.filter(slug=slug).first()
        if project is None:
            continue

        project.skills.add(capability)
        if options["drop_automation"] and automation is not None:
            project.skills.remove(automation)

    # --- 2. renames ---------------------------------------------------------
    for old_name, new_name, new_slug in RENAMES:
        skill = Skill.objects.filter(skill__iexact=old_name).first()
        if skill is None or Skill.objects.filter(skill__iexact=new_name).exists():
            continue

        skill.skill = new_name
        skill.slug = unique_slug(Skill, new_slug)
        skill.save(update_fields=["skill", "slug"])

    # --- 3. retire the generic AI tag --------------------------------------
    for name in RETIRE:
        for skill in Skill.objects.filter(skill__iexact=name):
            skill.projects.clear()
            skill.delete()

    for name, category, order in ADD_TOOLS:
        if Skill.objects.filter(skill__iexact=name).exists():
            continue

        Skill.objects.create(skill=name, category=category, sort_order=order,
                             slug=unique_slug(Skill, slugify(name)))


def backwards(apps, schema_editor):
    """Reverses the renames and removes what was added.

    The AI capability is only removed while nothing references it, so a
    rollback cannot silently discard tagging done since.
    """
    Skill = apps.get_model("main", "Skill")

    for old_name, new_name, _ in RENAMES:
        skill = Skill.objects.filter(skill__iexact=new_name).first()
        if skill is None:
            continue

        skill.skill = old_name
        skill.slug = unique_slug(Skill, slugify(old_name))
        skill.save(update_fields=["skill", "slug"])

    for name, _, _ in ADD_TOOLS:
        for skill in Skill.objects.filter(skill__iexact=name):
            if not skill.projects.exists():
                skill.delete()

    for skill in Skill.objects.filter(skill__iexact=AI_CAPABILITY):
        if not skill.projects.exists():
            skill.delete()


class Migration(migrations.Migration):

    dependencies = [("main", "0010_project_publishing_and_outcome")]

    operations = [migrations.RunPython(forwards, backwards)]
