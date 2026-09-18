from django.db import migrations, models


def seed_is_personal(apps, schema_editor):
    """Carries the old heuristic forward so nothing changes on the page.

    Personal/Professional used to be derived from whether githubLink was set.
    Seeding from that keeps every existing project categorised exactly as it was
    before; they can be corrected individually in the admin afterwards.
    """
    Project = apps.get_model("main", "Project")

    Project.objects.filter(githubLink__isnull=False).exclude(githubLink="").update(is_personal=True)
    Project.objects.filter(githubLink__isnull=True).update(is_personal=False)
    Project.objects.filter(githubLink="").update(is_personal=False)


def restore_from_github_link(apps, schema_editor):
    """No-op: reversing drops the column, and githubLink still holds the signal."""


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0002_project_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="is_personal",
            field=models.BooleanField(
                default=True,
                help_text="Personal projects are shown in the accent colour; professional ones in purple.",
                verbose_name="Personal project"),
        ),
        migrations.RunPython(seed_is_personal, restore_from_github_link),

        # Dead since it was reintroduced: the flag is False on every row and the
        # template it selected, project_html.html, was an empty stub.
        migrations.RemoveField(
            model_name="project",
            name="html_project",
        ),
    ]
