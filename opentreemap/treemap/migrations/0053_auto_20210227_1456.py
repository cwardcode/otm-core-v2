# Generated by Django 3.1.7 on 2021-02-27 20:56

import django.contrib.auth.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('treemap', '0052_merge_20210227_1454'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='neighborhoodgroup',
            managers=[
                ('objects', django.contrib.auth.models.GroupManager()),
            ],
        ),
        migrations.AddField(
            model_name='species',
            name='is_common',
            field=models.NullBooleanField(verbose_name='Is Common Species'),
        ),
    ]