"""Admin help text only: the portfolio heading was renamed to "Featured
work", and the checkbox's help text still pointed at "Selected work".

No schema change -- help_text lives in the migration state, so Django
asks for this even though the column is untouched.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_job_responsibilities'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='featured',
            field=models.BooleanField(default=False, help_text="Featured projects lead the portfolio page under 'Featured work'."),
        ),
    ]
