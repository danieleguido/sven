# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sven', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='corpus',
            field=models.ForeignKey(related_name='tags', blank=True, to='sven.Corpus', null=True),
        ),
    ]
