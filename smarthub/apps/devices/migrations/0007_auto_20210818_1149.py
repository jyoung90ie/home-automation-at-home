# Generated by Django 3.2.5 on 2021-08-18 10:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("devices", "0006_alter_device_location"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="devicelocation",
            options={},
        ),
        migrations.AddConstraint(
            model_name="devicelocation",
            constraint=models.UniqueConstraint(
                fields=("user", "location"), name="user_device_location"
            ),
        ),
    ]