# Generated by Django 3.2.5 on 2021-08-28 18:04

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("devices", "0008_auto_20210818_1206"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeviceState",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("device_object_id", models.PositiveBigIntegerField()),
                (
                    "name",
                    models.CharField(
                        max_length=50,
                        verbose_name="How would you like to refer to this state?",
                    ),
                ),
                (
                    "command",
                    models.CharField(
                        max_length=100,
                        verbose_name="What is the command name that invokes the state change in your device?",
                    ),
                ),
                (
                    "command_value",
                    models.CharField(
                        max_length=100,
                        verbose_name="What state value should be sent to your device?",
                    ),
                ),
                (
                    "device_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "abstract": False,
            },
        ),
    ]