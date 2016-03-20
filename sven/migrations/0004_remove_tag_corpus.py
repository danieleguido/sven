# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sven', '0003_auto_20160319_1253'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tag',
            name='corpus',
        ),
    ]
