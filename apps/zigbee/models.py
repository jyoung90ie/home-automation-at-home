"""Specifies data models for creating and storing information from zigbee devices"""
import json
import logging
from json.decoder import JSONDecodeError
from typing import TYPE_CHECKING, Union

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models.query_utils import Q

from ..models import BaseAbstractModel
from ..mqtt.publish import send_messages
from ..notifications.models import NotificationMedium

if TYPE_CHECKING:
    from ..devices.models import Device
    from ..events.models import EventTrigger, EventTriggerLog

logger = logging.getLogger("mqtt")
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
    def process_metadata(cls, metadata):
        """If mqtt data type is an interview then capture metadata for model"""
        message_type = metadata.get("type")
        if message_type and message_type == cls.INTERVIEW_TYPE:
            data = metadata.get("data")
            ieee_address = data.get("ieee_address")

            if not ieee_address:
                return

            zigbee_device: "ZigbeeDevice" = cls.objects.filter(
                ieee_address=ieee_address
            )

            if not zigbee_device:
                logger.info("Found new device with IEEE Address ='%s'", ieee_address)
                return cls.create_device(metadata)

    @staticmethod
    def dict_generator(fields, data, _dict=None):
        """Returns a dict containing specified data fields"""
        if not _dict:
            _dict = {}

        for field in fields:
            _dict[field] = data.get(field)

        return _dict

    @classmethod
    def create_device(cls, metadata):
        """Creates new zigbee device based on information provided by MQTT broker"""
        logger.info("ZigbeeDevice metadata=%s", metadata)

        if not metadata:
            logger.info(
                "Could not create new zigbee device as metadata did not contain any data"
            )
            return

        device_dict = cls.dict_generator(cls.DATA_FIELDS, metadata)
        definition_data = metadata.get("definition")

        if definition_data:
            device_dict = cls.dict_generator(
                cls.DEFINITION_DATA_FIELDS, definition_data, device_dict
            )

        zigbee_device = cls.objects.create(**device_dict)
        if zigbee_device:
            logger.info(
                "Zigbee device created: friendly_name=%s - ieee_address=%s'",
                device_dict["friendly_name"],
                device_dict["ieee_address"],
            )

            cls.link_to_user_device(zigbee_device)
            return zigbee_device

        logger.error("Could not create ZigbeeDevice for %s", device_dict)
        return None

    @classmethod
    def link_to_user_device(cls, zigbee_device=None) -> bool:
        """Attempt to match zigbee device to an entry in Device model"""
        try:
            if not cls.user_device_model:
                return

            obj = zigbee_device or cls
            logger.info("ZigbeeDevice - link_device - obj=%s", obj)

            if not obj.device:
                device = cls.user_device_model.objects.filter(
                    models.Q(friendly_name=obj.friendly_name)
                    | models.Q(friendly_name=obj.ieee_address)
                )

                if device:
                    cls.device = device
                    obj.save()
                    logger.info(
                        "Zigbee device (friendly_name=%s) linked to user device uuid='%s'",
                        obj.friendly_name,
                        obj.device.uuid,
                    )
                    return True
                logger.info(
                    "Could not link device (friendly_name=%s) as no user device exists",
                    obj.friendly_name,
                )
        except Exception as ex:
            logger.error("ERROR: ZigbeeDevice link_to_user_device - %s", ex)
        return False

    def __str__(self) -> str:
        return f"{self.friendly_name} ({self.ieee_address})"

    @property
    def user_device(self) -> Union["Device", None]:
        """Returns user device if it exists, otherwise None"""
        return getattr(self, "device", None)

    def save(self, *args, **kwargs):
        # save lowercase to maintain consistency with MQTT broker
        self.friendly_name = self.friendly_name.lower()
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

    def check_event_triggers(self, last_message=None):
        """Checks if linked device is attached to event trigger - if so, values check and event
        triggered if necessary"""

        self.user_device = getattr(self.zigbee_device, "user_device", False)

        if not self.user_device:
            return

        self.user = getattr(self.user_device, "user", None)

        triggers = self.user_device.get_event_triggers()

        if not triggers:
            logger.info(
                "%s - ZigbeeMessage - check_event_triggers - no event triggers",
                __name__,
            )
            return

        try:
            parsed_message = json.loads(self.raw_message)
        except JSONDecodeError:
            logger.info(
                "%s - ZigbeeMessage - check_event_triggers - could not parse message JSON",
                __name__,
            )
            return

        for trigger in triggers:
            self.process_event_trigger(
                parsed_message=parsed_message,
                trigger=trigger,
                last_message=last_message,
            )

    def process_event_trigger(
        self, parsed_message: dict, trigger: "EventTrigger", last_message=None
    ):
        """Processes event triggers and invokes notifications/event responses if criteria met"""
        logger.info("%s - process_event_trigger - start", __name__)
        field = getattr(trigger, "metadata_field")
        device_value = str(parsed_message.get(field, None)).lower()

        if not device_value or device_value is None:
            return

        if last_message:
            # only check if last_message has a value
            last_message = json.loads(last_message)

            cached_value = str(last_message.get(field, None)).lower()

            if device_value == cached_value:
                logger.info(
                    "process_event_trigger: device field value is unchanged - ignoring "
                    "[last: %s, curr: %s]",
                    cached_value,
                    device_value,
                )
                # the actual trigger value hasn't changed
                return

        event = getattr(trigger, "event")
        if not event.is_enabled:
            logger.info(
                "process_event_trigger - event is disabled (triggers and notifications will "
                "not be processed)"
            )
            return

        trigger_result = trigger.is_triggered(device_value)

        if trigger_result:
            # matched a trigger - record notification
            message = (
                f"{event.notification_message}\n\nTriggered by={trigger}\n\n"
                "Device value={device_value}"
            )

            trigger_log = self.invoke_event_response(triggered_by=trigger)

            if event.send_notification:
                self.invoke_notifications(
                    topic=event.notification_topic,
                    message=message,
                    triggered_by=trigger,
                    trigger_log=trigger_log,
                )

        logger.info("process_event_trigger end")

    def invoke_event_response(self, triggered_by: "EventTrigger"):
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
    ):
        """Invoke all of user's enabled notifications"""
        if not self.user:
            logger.info("invoke_notifications: no user object - cannot proceed")
            return

        user_notifications = get_user_model().objects.get_active_notifications(
            user=self.user
        )
        if not user_notifications:
            logger.info("invoke_notifications: user has no active notification mediums")

            return

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

        logger.info("Notification invocation complete.")


class ZigbeeLog(BaseAbstractModel):
    """Captures metadata from MQTT subscription messages"""

    broker_message = models.ForeignKey(ZigbeeMessage, on_delete=models.CASCADE)
    metadata_type = models.CharField(max_length=100)
    metadata_value = models.JSONField(max_length=100)

    def __str__(self):
        return f"{self.metadata_type}={self.metadata_value}"