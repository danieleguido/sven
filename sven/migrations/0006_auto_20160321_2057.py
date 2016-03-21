# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sven', '0005_auto_20160321_2054'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='corpus',
            name='pos',
        ),
        migrations.AddField(
            model_name='corpus',
            name='partofspeech',
            field=models.CharField(default=b'NP', max_length=32, blank=True),
        ),
        migrations.AlterField(
            model_name='segment',
            name='partofspeech',
            field=models.CharField(max_length=3, choices=[(b'NP', 'noun phrase'), (b'JJ', 'all adjectives'), (b'NN', 'all nouns'), (b'VP', 'verb phrases')]),
        ),
    ]
