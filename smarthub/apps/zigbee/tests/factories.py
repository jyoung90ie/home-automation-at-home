import factory
from django.db.models.signals import post_save

from ...users.tests.factories import UserFactory
from ...devices.tests.factories import DeviceFactory
from .. import models


@factory.django.mute_signals(post_save)
class ZigbeeDeviceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ZigbeeDevice

    uuid = factory.Faker("uuid4")
    device = factory.SubFactory(DeviceFactory)
    friendly_name = factory.Faker("name")
    ieee_address = factory.Faker("isbn")
    vendor = factory.Sequence(lambda n: "vendor %s" % n)
    model = factory.Faker("name")
    model_id = factory.fuzzy.FuzzyText(length=6, prefix="MODEL-")
    power_source = factory.fuzzy.FuzzyChoice(["Battery", "Mains"])


@factory.django.mute_signals(post_save)
class ZigbeeMessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ZigbeeMessage


@factory.django.mute_signals(post_save)
class ZigbeeLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ZigbeeMessage

    broker_message = factory.SubFactory(ZigbeeMessageFactory)
