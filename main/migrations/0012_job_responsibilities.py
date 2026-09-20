"""Moves job bullets off the JobDetail table and onto the job itself.

A bullet had one field, no ordering, no fields of its own and nothing
referencing it. JobDetail also declared no ordering and the view never asked
for one, so the SQL carried no ORDER BY and the rendered order was whatever
SQLite happened to return. The backfill freezes that apparent order -- primary
key, which is insertion order -- so the page reads exactly as it did before.

The table is not dropped here. It keeps its rows for one release so the
backfill can be checked against the live page, and a later migration removes
it.

Reversible: backwards clears the field and rebuilds the rows by splitting on
newlines, which is lossless for the data as it stands (no bullet contains a
newline).
"""
from django.db import migrations, models


def forwards(apps, schema_editor):
    Job = apps.get_model("main", "Job")
    JobDetail = apps.get_model("main", "JobDetail")

    for job in Job.objects.all():
        # Assignment, not append, so a re-run cannot double the bullets. What
        # it would do is overwrite text edited since the backfill with the
        # stale JobDetail rows, which is what this skips -- the table is still
        # sitting there for the rollback window, holding the old wording.
        if job.responsibilities.strip():
            continue

        lines = [detail.content.strip()
                 for detail in JobDetail.objects.filter(relatedJob=job).order_by("pk")
                 if detail.content.strip()]

        if not lines:
            continue

        job.responsibilities = "\n".join(lines)
        job.save(update_fields=["responsibilities"])


def backwards(apps, schema_editor):
    Job = apps.get_model("main", "Job")
    JobDetail = apps.get_model("main", "JobDetail")

    for job in Job.objects.all():
        lines = [line.strip()
                 for line in job.responsibilities.splitlines()
                 if line.strip()]

        if not lines:
            continue

        # The rows are still there from the forward run, so rebuilding without
        # clearing first would double them.
        JobDetail.objects.filter(relatedJob=job).delete()

        for line in lines:
            JobDetail.objects.create(relatedJob=job, content=line)

        job.responsibilities = ""
        job.save(update_fields=["responsibilities"])


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0011_taxonomy_refresh"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="jobdetail",
            options={"ordering": ("pk",)},
        ),
        migrations.AddField(
            model_name="job",
            name="responsibilities",
            field=models.TextField(
                blank=True,
                help_text="One bullet per line. Blank lines are ignored. The "
                          "order you type is the order the page renders."),
        ),
        migrations.RunPython(forwards, backwards),
    ]
