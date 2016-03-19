# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import sven.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Corpus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=32)),
                ('slug', models.CharField(unique=True, max_length=32)),
                ('color', models.CharField(max_length=6, blank=True)),
                ('date_last_modified', models.DateTimeField(auto_now=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('owners', models.ManyToManyField(related_name='corpora', to=settings.AUTH_USER_MODEL)),
                ('watchers', models.ManyToManyField(related_name='corpora_watched', to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'verbose_name_plural': 'corpora',
            },
        ),
        migrations.CreateModel(
            name='Distance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cosine_similarity', models.FloatField(default=b'0')),
            ],
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('slug', models.CharField(unique=True, max_length=128)),
                ('abstract', models.CharField(max_length=160, null=True, blank=True)),
                ('language', models.CharField(max_length=2, choices=[(b'en', 'english'), (b'fr', 'french'), (b'nl', 'dutch'), (b'it', 'italian'), (b'es', 'spanish')])),
                ('raw', models.FileField(max_length=200, null=True, upload_to=sven.models.helper_get_document_path, blank=True)),
                ('mimetype', models.CharField(max_length=100, null=True, blank=True)),
                ('date', models.DateTimeField(null=True, blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_last_modified', models.DateTimeField(auto_now=True)),
                ('url', models.URLField(max_length=255, null=True, blank=True)),
                ('corpus', models.ForeignKey(related_name='documents', to='sven.Corpus')),
            ],
        ),
        migrations.CreateModel(
            name='Document_Segment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tf', models.FloatField(default=0)),
                ('wf', models.FloatField(default=0)),
                ('tfidf', models.FloatField(default=0)),
                ('document', models.ForeignKey(related_name='document_segments', to='sven.Document')),
            ],
        ),
        migrations.CreateModel(
            name='DocumentInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_last_modified', models.DateTimeField(auto_now=True)),
                ('date_indexed', models.DateTimeField(null=True, blank=True)),
                ('date_deleted', models.DateTimeField(null=True, blank=True)),
                ('date_texified', models.DateTimeField(null=True, blank=True)),
                ('date_analyzed', models.DateTimeField(null=True, blank=True)),
                ('document', models.OneToOneField(related_name='info', to='sven.Document')),
            ],
        ),
        migrations.CreateModel(
            name='Entity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.CharField(max_length=128)),
                ('url', models.URLField(unique=True)),
                ('type', models.CharField(default=b'', max_length=3, choices=[(b'Per', b'person'), (b'Pla', b'place'), (b'Org', b'organisation')])),
            ],
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pid', models.CharField(max_length=32)),
                ('cmd', models.TextField()),
                ('status', models.CharField(default=b'BOO', max_length=3, choices=[(b'BOO', 'started'), (b'RUN', 'running'), (b'RIP', 'process not found'), (b'END', 'job completed'), (b'ERR', 'job error')])),
                ('completion', models.FloatField(default=b'0')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_last_modified', models.DateTimeField(auto_now=True)),
                ('corpus', models.OneToOneField(related_name='job', null=True, to='sven.Corpus')),
                ('document', models.ForeignKey(blank=True, to='sven.Document', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bio', models.TextField(null=True, blank=True)),
                ('picture', models.URLField(max_length=160, null=True, blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_last_modified', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Segment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.CharField(max_length=128)),
                ('lemmata', models.CharField(max_length=128)),
                ('cluster', models.CharField(max_length=128)),
                ('language', models.CharField(max_length=2, choices=[(b'en', 'english'), (b'fr', 'french'), (b'nl', 'dutch'), (b'it', 'italian'), (b'es', 'spanish')])),
                ('status', models.CharField(default=b'IN', max_length=3, choices=[(b'OUT', 'exclude'), (b'IN', 'include')])),
                ('partofspeech', models.CharField(max_length=3, choices=[(b'NP', 'noun phrase')])),
                ('corpus', models.ForeignKey(related_name='segments', to='sven.Corpus')),
                ('entity', models.ForeignKey(related_name='segments', blank=True, to='sven.Entity', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Sentence',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField()),
                ('position', models.IntegerField()),
                ('document', models.ForeignKey(to='sven.Document')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('slug', models.SlugField(unique=True, max_length=128)),
                ('type', models.CharField(max_length=32)),
            ],
            options={
                'managed': True,
            },
        ),
        migrations.AddField(
            model_name='document_segment',
            name='segment',
            field=models.ForeignKey(related_name='document_segments', to='sven.Segment'),
        ),
        migrations.AddField(
            model_name='document',
            name='segments',
            field=models.ManyToManyField(to='sven.Segment', null=True, through='sven.Document_Segment', blank=True),
        ),
        migrations.AddField(
            model_name='document',
            name='tags',
            field=models.ManyToManyField(related_name='tagdocuments', null=True, to='sven.Tag', blank=True),
        ),
        migrations.AddField(
            model_name='distance',
            name='alpha',
            field=models.ForeignKey(related_name='alpha', to='sven.Document'),
        ),
        migrations.AddField(
            model_name='distance',
            name='omega',
            field=models.ForeignKey(related_name='omega', to='sven.Document'),
        ),
        migrations.AlterUniqueTogether(
            name='segment',
            unique_together=set([('content', 'corpus', 'partofspeech')]),
        ),
        migrations.AlterUniqueTogether(
            name='document_segment',
            unique_together=set([('segment', 'document')]),
        ),
        migrations.AlterUniqueTogether(
            name='distance',
            unique_together=set([('alpha', 'omega')]),
        ),
    ]
