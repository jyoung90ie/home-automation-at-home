# Generated by Django 3.2.5 on 2021-08-09 14:15

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DeviceLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', models.CharField(max_length=100)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('friendly_name', models.CharField(max_length=150)),
                ('device_identifier', models.CharField(max_length=255)),
                ('protocol', models.CharField(choices=[('API', 'API'), ('ZIGBEE', 'Zigbee')], default='API', max_length=10)),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='devices.devicelocation')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='device',
            constraint=models.UniqueConstraint(fields=('user', 'device_identifier'), name='user_device'),
        ),
    ]
