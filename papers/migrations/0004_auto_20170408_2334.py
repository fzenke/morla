# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-09 06:34
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0003_auto_20170408_1112'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='article',
            unique_together=set([]),
        ),
    ]
