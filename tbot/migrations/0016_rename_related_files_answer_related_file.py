# Generated by Django 5.1.4 on 2024-12-12 16:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tbot', '0015_remove_answer_duration_seconds_answer_duration'),
    ]

    operations = [
        migrations.RenameField(
            model_name='answer',
            old_name='related_files',
            new_name='related_file',
        ),
    ]
