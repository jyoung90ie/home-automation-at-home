from django.db.models.signals import post_save

import factory
from factory import fuzzy

from ...users.tests.factories import UserFactory
from ...devices.tests.factories import DeviceFactory, ZigbeeDeviceStateFactory
from .. import models


@factory.django.mute_signals(post_save)
class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Event

    user = factory.SubFactory(UserFactory)
    description = factory.Faker("sentence")
    is_enabled = factory.Faker("boolean")
    send_notification = factory.Faker("boolean")
    notification_topic = factory.Faker("sentence")
    notification_message = factory.Faker("sentence")


@factory.django.mute_signals(post_save)
class EventTriggerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.EventTrigger

    event = factory.SubFactory(EventFactory)
    device = factory.SubFactory(DeviceFactory)
    metadata_field = fuzzy.FuzzyChoice(
        [
            "linkquality",
            "state",
            "temperature",
            "humidity",
            "battery_low",
            "battery",
            "occupancy",
        ]
    )
    metadata_trigger_value = fuzzy.FuzzyChoice(
        [
            "on",
            "off",
            "true",
            "false",
            "100",
            "80",
            "60",
            "40",
            "20",
            "0",
        ]
    )
    trigger_type = fuzzy.FuzzyChoice(models.EventTriggerType)
    is_enabled = factory.Faker("boolean")


@factory.django.mute_signals(post_save)
class EventResponseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.EventResponse

    event = factory.SubFactory(EventFactory)
    device_state = factory.SubFactory(ZigbeeDeviceStateFactory)
    is_enabled = factory.Faker("boolean")


@factory.django.mute_signals(post_save)
class EventTriggerLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.EventTriggerLog

    event = factory.SubFactory(EventFactory)
    # triggered_by = factory.Faker("company")
    # response_command = factory.Faker("word")
