# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('partner', '0007_auto_20150914_0841'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partner',
            name='short_code',
            field=models.CharField(unique=True, max_length=8),
        ),
    ]
