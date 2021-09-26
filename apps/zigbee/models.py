"""Specifies data models for creating and storing information from zigbee devices"""
import json
import logging
from json.decoder import JSONDecodeError
from typing import TYPE_CHECKING, Tuple, Union

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models.query_utils import Q

from ..devices.models import DeviceProtocol
from ..models import BaseAbstractModel
from ..mqtt.publish import send_messages
from ..notifications.models import NotificationMedium

if TYPE_CHECKING:
    from ..devices.models import Device
    from ..events.models import EventTrigger, EventTriggerLog

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

METADATA_TYPE_FIELD = "zigbeemessage__zigbeelog__metadata_type"


class ZigbeeDeviceQuerySet(models.QuerySet):
    """Custom queries"""

    def get_metadata_fields(self, device) -> models.QuerySet:
        """Return list of unique metadata values for the specified device"""
        return (
            self.filter(device=device)
            .order_by(METADATA_TYPE_FIELD)
            .values_list(METADATA_TYPE_FIELD, flat=True)
            .distinct()
        )

    def get_device_states(self, device) -> models.QuerySet:
        """Return list of user created states for the specified device"""
        return self.filter(device=device).values(
            "device_states__uuid", "device_states__name"
        )


class ZigbeeDeviceManager(models.Manager.from_queryset(ZigbeeDeviceQuerySet)):
    """Custom manager"""


class ZigbeeDevice(BaseAbstractModel):
    """Captures zigbee device metadata and makes connection to user device"""

    INTERVIEW_TYPE = "device_interview"

    # data to capture from mqtt
    DATA_FIELDS = ["friendly_name", "ieee_address", "model_id", "power_source"]
    DEFINITION_DATA_FIELDS = ["description", "model", "vendor"]

    user_device_model = None

    objects = ZigbeeDeviceManager()

    device = models.ForeignKey(
        "devices.Device", on_delete=models.SET_NULL, blank=True, null=True
    )

    device_states = GenericRelation(
        "devices.DeviceState",
        object_id_field="device_object_id",
        content_type_field="device_type",
        related_query_name="zigbee",
    )

    friendly_name = models.CharField(max_length=100, blank=True, null=True)
    ieee_address = models.CharField(max_length=100, blank=True, null=True)
    description = models.CharField(max_length=100, blank=True, null=True)
    vendor = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    model_id = models.CharField(max_length=100, blank=True, null=True)
    power_source = models.CharField(max_length=100, blank=True, null=True)
    is_controllable = models.BooleanField(default=False)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.user_device_model = apps.get_model("devices", "Device")

    @classmethod
    def process_metadata(cls, metadata: dict) -> Union["ZigbeeDevice", None]:
        """If mqtt data type is an interview then capture metadata for model"""
        message_type = metadata.get("type")
        if message_type and message_type == cls.INTERVIEW_TYPE:
            data = metadata.get("data")

            if not data:
                logger.info(
                    "%s - cannot process metadata without `data` dict", __name__
                )
                return

            ieee_address = data.get("ieee_address", False)

            if not ieee_address:
                logger.info(
                    "%s - cannot process metadata without `ieee_address`", __name__
                )
                return

            zigbee_device: "ZigbeeDevice" = cls.objects.filter(
                ieee_address=ieee_address
            )

            if not zigbee_device:
                logger.info("Found new device with `ieee_address`='%s'", ieee_address)
                return cls.create_device(metadata=data)

    @staticmethod
    def dict_generator(fields, data, _dict=None) -> dict:
        """Returns a dict containing specified data fields"""
        if not _dict:
            _dict = {}

        for field in fields:
            _dict[field] = data.get(field)

        return _dict

    @classmethod
    def create_device(cls, metadata: dict) -> Union["ZigbeeDevice", None]:
        """Creates new zigbee device based on information provided by MQTT broker"""
        logger.info("ZigbeeDevice metadata=%s", metadata)

        if not metadata:
            logger.info(
                "Could not create new zigbee device as metadata did not contain any data"
            )
            return

        device_dict = cls.dict_generator(fields=cls.DATA_FIELDS, data=metadata)
        definition_data = metadata.get("definition", None)

        if definition_data:
            device_dict = cls.dict_generator(
                fields=cls.DEFINITION_DATA_FIELDS,
                data=definition_data,
                _dict=device_dict,
            )

        zigbee_device = cls.objects.create(**device_dict)
        if zigbee_device:
            logger.info(
                "Zigbee device created: friendly_name=%s - ieee_address=%s'",
                device_dict["friendly_name"],
                device_dict["ieee_address"],
            )

            zigbee_device.try_to_link_user_device()

            return zigbee_device

        logger.error("Could not create ZigbeeDevice for %s", device_dict)
        return None

    def try_to_link_user_device(self) -> bool:
        """Attempt to match zigbee device to an entry in Device model"""
        is_linked = False
        try:
            if not self.user_device_model:
                return is_linked

            if not self.device:
                device = self.user_device_model.objects.filter(
                    models.Q(friendly_name=self.friendly_name)
                    | models.Q(device_identifier=self.ieee_address),
                    protocol=DeviceProtocol.ZIGBEE,
                ).first()

                if device:
                    self.device = device
                    self.save()
                    logger.info(
                        "Zigbee device (friendly_name=%s) linked to user device uuid='%s'",
                        self.friendly_name,
                        self.device.uuid,
                    )
                    return True
                logger.info(
                    "Could not link device (friendly_name=%s) as no user device exists",
                    self.friendly_name,
                )
        except Exception as ex:
            logger.error("link_to_user_device - %s", ex)

        return is_linked

    def __str__(self) -> str:
        return f"{self.friendly_name} ({self.ieee_address})"

    @property
    def user_device(self) -> Union["Device", None]:
        """Returns user device if it exists, otherwise None"""
        return getattr(self, "device", None)

    def save(self, *args, **kwargs):
        # save lowercase to maintain consistency with MQTT broker
        if self.friendly_name:
            self.friendly_name = self.friendly_name.lower()
        if self.ieee_address:
            self.ieee_address = self.ieee_address.lower()

        super().save(*args, **kwargs)


class ZigbeeMessage(BaseAbstractModel):
    """Creates an entry to link an MQTT subscription message to a device and metadata"""

    zigbee_device = models.ForeignKey(
        ZigbeeDevice, on_delete=models.CASCADE, null=True, blank=True
    )
    raw_message = models.JSONField()
    topic = models.CharField(max_length=255)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.user = None
        self.user_device = None
        self.message = None

    def link_to_zigbee_device(self) -> None:
        """Attempts to match object to a ZigbeeDevice, if matched the zigbee_device field is set
        and the object is saved. IMPORTANT - this method is called from obj.save() - do NOT call
        self.save() here or it will invoke a recursive loop.

        Matching messages to devices is conducted by by matching MQTT topic to user device
         device_identifier. If no match is found, an attempt is made using the device
         friendly_name."""
        try:
            topic_beginning = self.topic.rfind("/") + 1
            usable_topic = self.topic[topic_beginning:].strip()
            usable_topic = str(usable_topic).lower()

            zigbee_device = ZigbeeDevice.objects.filter(
                Q(ieee_address=usable_topic) | Q(friendly_name=usable_topic)
            ).first()

            self.zigbee_device = zigbee_device
        except ZigbeeDevice.DoesNotExist:
            pass

    def __str__(self):
        return str(self.topic)

    def save(self, *args, check_triggers=None, last_message=None, **kwargs) -> None:
        """
        Parameters:
            check_triggers - when True will perform event trigger checks & invoke event
             response(s) if necessary

        Provides additional logic for:
        1) Linking ZigbeeMessage (self) to ZigbeeDevice via link_to_zigbee_device()
        1) Checks if Device is linked to an EventTrigger
        """
        # methods modifying object that need to be performed pre-save
        self.link_to_zigbee_device()
        super().save(*args, **kwargs)

        # methods accessing object attributes that need to be perform post-save
        if check_triggers:
            logger.info("%s - Checking event triggers...", __name__)
            self.check_event_triggers(last_message=last_message)
            logger.info("%s - End of event trigger checks.", __name__)

    def check_event_triggers(self, last_message=None) -> None:
        """Checks if linked device is attached to event trigger - if so, values check and event
        triggered if necessary"""

        self.user_device = getattr(self.zigbee_device, "user_device", False)

        if not self.user_device:
            return

        self.user = getattr(self.user_device, "user", None)

        # only returns enabled triggers
        triggers = self.user_device.get_event_triggers()

        if not triggers:
            logger.info(
                "%s - ZigbeeMessage - check_event_triggers - no event triggers",
                __name__,
            )
            return

        try:
            parsed_message = json.loads(self.raw_message)
        except JSONDecodeError as ex:
            logger.info("%s - ZigbeeMessage - check_event_triggers - %s", __name__, ex)
            return

        processed_notifications = []
        for trigger in triggers:
            if not trigger.event.is_enabled or not trigger.is_enabled:
                # skip disabled events and triggers
                continue

            # check to see if event notifications have already been processed
            process_notifications = trigger.event.uuid not in processed_notifications

            _, notifications_invoked = self.process_event_trigger(
                parsed_message=parsed_message,
                trigger=trigger,
                cached_message=last_message,
                process_notifications=process_notifications,
            )

            if notifications_invoked:
                processed_notifications.append(trigger.event.uuid)

    def process_event_trigger(
        self,
        parsed_message: dict,
        trigger: "EventTrigger",
        cached_message=None,
        process_notifications=True,
    ) -> Tuple[bool, bool]:
        """Processes event triggers and invokes notifications/event responses if criteria met.

        Returns a tuple = response_invoked, notifications_invoked"""
        logger.info("%s - process_event_trigger - start", __name__)

        response_invoked = False
        notifications_invoked = False

        field = getattr(trigger, "metadata_field")
        event = getattr(trigger, "event")
        device_value = str(parsed_message.get(field, None)).lower()

        if (
            not device_value
            or not event.is_enabled
            or not self.device_value_changed(
                cached_message=cached_message,
                field=field,
                device_value=device_value,
            )
        ):
            # skip empty values, disabled events, and unchanged device values
            return response_invoked, notifications_invoked
        trigger_result = trigger.is_triggered(device_value)
        if trigger_result:
            # matched a trigger - record notification
            message = (
                f"{event.notification_message}\n\nTriggered by={trigger}\n\n"
                f"Device value={device_value}"
            )

            trigger_log = self.invoke_event_response(triggered_by=trigger)
            response_invoked = trigger_log is not None

            if process_notifications and event.send_notification:
                notifications_invoked = True
                self.invoke_notifications(
                    topic=event.notification_topic,
                    message=message,
                    triggered_by=trigger,
                    trigger_log=trigger_log,
                )

        logger.info("process_event_trigger end")
        return response_invoked, notifications_invoked

    def device_value_changed(
        self, cached_message: str, field: str, device_value: str
    ) -> bool:
        """Compare device value to cached value.

        Return true if values are different - i.e. have changed."""
        # only check if a previous message exists
        if not cached_message:
            return True
        cached_message = json.loads(cached_message)
        cached_value = str(cached_message.get(field, None)).lower()

        if device_value == cached_value:
            # the actual trigger value hasn't changed
            logger.info(
                "device field value is unchanged - ignoring last: %s, curr: %s]",
                cached_value,
                device_value,
            )
            return False

        return True

    def invoke_event_response(
        self, triggered_by: "EventTrigger"
    ) -> Union["EventTriggerLog", None]:
        """Invokes all EventResponse objects for a triggered Event.

        An event response essentially maps an event to a device state."""
        if not self.user:
            logger.info("invoke_event_response: no user object - cannot proceed")
            return
        event = getattr(triggered_by, "event", None)

        if not event:
            logger.error(
                "invoke_event_response: trigger is not attached to event - %s",
                triggered_by,
            )
            return

        event_responses = getattr(event, "eventresponse_set", None)
        if not event_responses:
            logger.error(
                "invoke_event_response: no event responses attached to event - %s",
                event,
            )
            return

        enabled_event_responses = event_responses.filter(is_enabled=True)

        cmd_list = []

        for response in enabled_event_responses:
            # invoke device states
            state = getattr(response, "device_state")
            cmd = getattr(state, "command")
            val = getattr(state, "command_value")
            device = getattr(state, "content_object")

            if not cmd or not val:
                logger.info(
                    "invoke_event_response: no command and/or value - cmd: %s - val: %s",
                    cmd,
                    val,
                )
                return

            cmd_dict = {
                "mqtt_topic": device.friendly_name,
                "command": cmd,
                "command_value": val,
            }
            cmd_list.append(cmd_dict)

        # cmd list is built and sent to MQTT broker
        try:
            logger.info(
                "%s - publishing messages to MQTT broker - %s", __name__, cmd_list
            )
            send_messages(cmd_list)

            trigger_log = apps.get_model("events", "EventTriggerLog")

            log = trigger_log.objects.create(
                event=event, triggered_by=triggered_by, response_command=cmd_list
            )

            return log
        except Exception:
            logger.error(
                "%s - there was an error publishing to MQTT broker - operation failed",
                __name__,
            )

    def invoke_notifications(
        self,
        topic: str,
        message: str,
        triggered_by: "EventTrigger",
        trigger_log: "EventTriggerLog" = None,
    ) -> int:
        """Invoke all of user's enabled notifications.

        Returns the number of notifications sent"""
        notifications_sent = 0

        if not self.user:
            logger.info("no user object - cannot proceed")
            return notifications_sent

        user_notifications = get_user_model().objects.get_active_notifications(
            user=self.user
        )
        if not user_notifications:
            logger.info("user has no active notification mediums")
            return notifications_sent

        logger.info("Invoking notifications...")

        for notification in user_notifications:
            notification_data = {
                "topic": topic,
                "message": message,
                "triggered_by": triggered_by,
                "notification_obj": notification,
                "trigger_log": trigger_log,
            }

            if notification.notification_medium == NotificationMedium.PUSHBULLET:
                notification.pushbulletnotification.send(**notification_data)
            elif notification.notification_medium == NotificationMedium.EMAIL:
                notification.emailnotification.send(**notification_data)
            notifications_sent += 1

        logger.info("Notification invocation complete.")

        return notifications_sent


class ZigbeeLog(BaseAbstractModel):
    """Captures metadata from MQTT subscription messages"""

    broker_message = models.ForeignKey(ZigbeeMessage, on_delete=models.CASCADE)
    metadata_type = models.CharField(max_length=100)
    metadata_value = models.JSONField(max_length=100)

    def __str__(self):
        return f"{self.metadata_type}={self.metadata_value}"
