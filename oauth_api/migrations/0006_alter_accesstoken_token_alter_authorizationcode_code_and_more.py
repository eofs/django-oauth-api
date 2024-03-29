# Generated by Django 4.1.7 on 2023-03-01 11:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("oauth_api", "0005_alter_authorizationcode_code_alter_refreshtoken_token"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accesstoken",
            name="token",
            field=models.TextField(db_index=True),
        ),
        migrations.AlterField(
            model_name="authorizationcode",
            name="code",
            field=models.TextField(db_index=True),
        ),
        migrations.AlterField(
            model_name="refreshtoken",
            name="token",
            field=models.TextField(db_index=True),
        ),
    ]
