# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('treemap', '0043_udfs_default'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='species',
            name='udfs',
        ),
    ]
