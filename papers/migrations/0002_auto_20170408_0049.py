# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-08 07:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='authors',
            field=models.CharField(max_length=250),
        ),
    ]
