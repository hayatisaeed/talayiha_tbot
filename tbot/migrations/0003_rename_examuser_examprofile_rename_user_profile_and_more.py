# Generated by Django 5.1.4 on 2024-12-06 13:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tbot', '0002_alter_user_role'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ExamUser',
            new_name='ExamProfile',
        ),
        migrations.RenameModel(
            old_name='User',
            new_name='Profile',
        ),
        migrations.RenameModel(
            old_name='UserGroup',
            new_name='ProfileGroup',
        ),
        migrations.RenameModel(
            old_name='UserOlympiad',
            new_name='ProfileOlympiad',
        ),
    ]