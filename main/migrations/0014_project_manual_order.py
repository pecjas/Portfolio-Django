"""Adds the manual ordering override for the portfolio page.

Nullable with no default, so every existing project keeps the date-based
order it already had and nothing moves until a number is entered.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0013_featured_help_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='sort_order',
            field=models.PositiveIntegerField(blank=True, help_text='Leave blank for the default order, newest first. Give a number to pin a project to the top of its section: 1 before 2 before 3, and everything numbered sits above everything blank. Featured projects are still ordered separately from the rest.', null=True, verbose_name='Manual order'),
        ),
    ]
