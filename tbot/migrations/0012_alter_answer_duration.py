# Generated by Django 5.1.4 on 2024-12-12 16:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tbot', '0011_remove_answer_submission_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='duration',
            field=models.IntegerField(default=0),
        ),
    ]
