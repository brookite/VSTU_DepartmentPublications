# Generated by Django 5.0.6 on 2024-06-22 15:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0008_alter_tag_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="emailsubscriber",
            name="department",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="api.department",
            ),
        ),
    ]
