# Generated by Django 5.1.4 on 2024-12-12 16:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tbot', '0014_rename_answer_scoresheet_related_answer_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='answer',
            name='duration_seconds',
        ),
        migrations.AddField(
            model_name='answer',
            name='duration',
            field=models.DurationField(null=True),
        ),
    ]
