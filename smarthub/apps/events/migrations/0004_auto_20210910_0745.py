# Generated by Django 3.2.5 on 2021-09-10 06:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0003_eventtriggerlog'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='event',
            options={'ordering': ['created_at']},
        ),
        migrations.AlterModelOptions(
            name='eventtriggerlog',
            options={'ordering': ['created_at']},
        ),
    ]
