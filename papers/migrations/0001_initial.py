# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-08 07:41
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=250)),
                ('authors', models.CharField(max_length=500)),
                ('pubdate', models.DateField()),
                ('journal', models.CharField(max_length=250)),
                ('abstract', models.TextField()),
                ('keywords', models.CharField(blank=True, max_length=250)),
                ('url', models.URLField(blank=True)),
                ('doi', models.CharField(blank=True, max_length=128)),
                ('pmid', models.IntegerField(blank=True, null=True)),
                ('date_added', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Feature',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('index', models.IntegerField()),
                ('value', models.FloatField()),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='papers.Article')),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_traindata_update', models.DateTimeField()),
                ('last_prediction_run', models.DateTimeField()),
                ('ham', models.ManyToManyField(related_name='ham', to='papers.Article')),
                ('spam', models.ManyToManyField(related_name='spam', to='papers.Article')),
                ('starred', models.ManyToManyField(related_name='starred', to='papers.Article')),
            ],
        ),
        migrations.CreateModel(
            name='Recommendation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_added', models.DateTimeField()),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='papers.Article')),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='papers.Profile')),
            ],
        ),
        migrations.CreateModel(
            name='Similarity',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('value', models.FloatField()),
                ('a', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='a', to='papers.Article')),
                ('b', models.ForeignKey(db_index=False, on_delete=django.db.models.deletion.CASCADE, related_name='b', to='papers.Article')),
            ],
        ),
        migrations.AddField(
            model_name='profile',
            name='suggested',
            field=models.ManyToManyField(related_name='suggested', through='papers.Recommendation', to='papers.Article'),
        ),
        migrations.AddField(
            model_name='profile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='article',
            unique_together=set([('title', 'authors')]),
        ),
        migrations.AlterUniqueTogether(
            name='similarity',
            unique_together=set([('a', 'b')]),
        ),
        migrations.AlterUniqueTogether(
            name='feature',
            unique_together=set([('article', 'index')]),
        ),
    ]
