# Generated by Django 3.2.5 on 2021-08-12 13:50

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("devices", "0005_auto_20210810_1440"),
    ]

    operations = [
        migrations.CreateModel(
            name="ZigbeeDevice",
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
                    models.UUIDField(default=uuid.uuid4,
                                     editable=False, unique=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "friendly_name",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "ieee_address",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "description",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("vendor", models.CharField(blank=True, max_length=100, null=True)),
                ("model", models.CharField(blank=True, max_length=100, null=True)),
                ("model_id", models.CharField(blank=True, max_length=100, null=True)),
                (
                    "power_source",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "device",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="devices.device",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ZigbeeMessage",
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
                    models.UUIDField(default=uuid.uuid4,
                                     editable=False, unique=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("raw_message", models.JSONField()),
                ("topic", models.CharField(max_length=255)),
                (
                    "zigbee_device",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="zigbee.zigbeedevice",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ZigbeeLog",
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
                    models.UUIDField(default=uuid.uuid4,
                                     editable=False, unique=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("metadata_type", models.CharField(max_length=100)),
                ("metadata_value", models.JSONField(max_length=100)),
                (
                    "broker_message",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="zigbee.zigbeemessage",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "abstract": False,
            },
        ),
    ]
