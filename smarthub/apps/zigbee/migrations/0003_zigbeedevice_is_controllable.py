# Generated by Django 3.2.5 on 2021-09-08 19:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zigbee', '0002_alter_zigbeedevice_device'),
    ]

    operations = [
        migrations.AddField(
            model_name='zigbeedevice',
            name='is_controllable',
            field=models.BooleanField(default=False),
        ),
    ]
