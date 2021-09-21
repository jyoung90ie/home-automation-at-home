import factory
from factory import fuzzy

from .. import models


class NotificationSettingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.NotificationSetting

    user = factory.SubFactory("apps.users.tests.factories.UserFactory")
    notification_medium = fuzzy.FuzzyChoice(models.NotificationMedium)
    is_enabled = True


class NotificationLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.NotificationLog

    medium = factory.SubFactory(NotificationSettingFactory)
    topic = "topic"
    message = factory.Faker("sentence")
    triggered_by = factory.Faker("sentence")
    notification_topic = factory.Faker("sentence")
    trigger_log = factory.SubFactory(
        "apps.events.tests.factories.EventTriggerLogFactory"
    )


class PushbulletNotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PushbulletNotification

    notification = factory.SubFactory(NotificationSettingFactory)
    access_token = factory.Faker("uuid4")


class EmailNotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.EmailNotification

    notification = factory.SubFactory(NotificationSettingFactory)
    from_email = factory.Faker("email")
    to_email = factory.Faker("email")
