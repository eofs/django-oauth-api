# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from oauth_api.settings import oauth_api_settings


class Migration(migrations.Migration):

    dependencies = [
        ('oauth_api', '0002_auto_20150904_1155'),
        migrations.swappable_dependency(oauth_api_settings.APPLICATION_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='authorizationcode',
            name='application',
            field=models.ForeignKey(to=oauth_api_settings.APPLICATION_MODEL, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='refreshtoken',
            name='application',
            field=models.ForeignKey(to=oauth_api_settings.APPLICATION_MODEL, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='accesstoken',
            name='application',
            field=models.ForeignKey(to=oauth_api_settings.APPLICATION_MODEL, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
