from django.db import migrations, models
from django.utils.text import slugify


def populate_slugs(apps, schema_editor):
    """Fills in a unique slug for every project that predates this field."""
    Project = apps.get_model("main", "Project")
    taken = set()

    for project in Project.objects.all().order_by("pk"):
        base = slugify(project.title) or "project"
        slug = base
        suffix = 2

        while slug in taken:
            slug = f"{base}-{suffix}"
            suffix += 1

        taken.add(slug)
        project.slug = slug
        project.save(update_fields=["slug"])


def clear_slugs(apps, schema_editor):
    """No-op: reversing the migration drops the column anyway."""


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0001_initial"),
    ]

    operations = [
        # Added without the unique constraint so existing rows can share the
        # empty default, then backfilled, then tightened.
        migrations.AddField(
            model_name="project",
            name="slug",
            field=models.SlugField(blank=True, default="", max_length=220),
            preserve_default=False,
        ),
        migrations.RunPython(populate_slugs, clear_slugs),
        migrations.AlterField(
            model_name="project",
            name="slug",
            field=models.SlugField(blank=True, max_length=220, unique=True),
        ),
    ]
