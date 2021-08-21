"""Specifies data models for creating and storing information from zigbee devices"""
import logging

from django.apps import apps
from django.db import models
from django.db.models.query import QuerySet
from django.db.models.query_utils import Q

from ..models import BaseAbstractModel

logger = logging.getLogger("mqtt")
logging.basicConfig()

METADATA_TYPE_FIELD = "zigbeemessage__zigbeelog__metadata_type"


class ZigbeeDeviceQuerySet(models.QuerySet):
    """Custom queries"""

    def get_metadata_fields(self, device):
        """Return list of unique metadata values for the specified device"""
        return (
            self.filter(device=device)
            .order_by(METADATA_TYPE_FIELD)
            .values_list(METADATA_TYPE_FIELD, flat=True)
            .distinct()
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
    friendly_name = models.CharField(max_length=100, blank=True, null=True)
    ieee_address = models.CharField(max_length=100, blank=True, null=True)
    description = models.CharField(max_length=100, blank=True, null=True)
    vendor = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    model_id = models.CharField(max_length=100, blank=True, null=True)
    power_source = models.CharField(max_length=100, blank=True, null=True)

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
                logger.info(
                    "Found new device with IEEE Address ='%s'", ieee_address)
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
    def link_to_user_device(self, zigbee_device=None) -> bool:
        """Attempt to match zigbee device to an entry in Device model"""
        try:
            if not self.user_device_model:
                return

            obj = zigbee_device or self
            logger.info(f"ZigbeeDevice - link_device - obj={obj}")

            if not obj.device:
                device = self.user_device_model.objects.filter(
                    models.Q(friendly_name=obj.friendly_name)
                    | models.Q(friendly_name=obj.ieee_address)
                )

                if device:
                    self.device = device
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
            logger.error("ERROR: ZigbeeDevice link_to_user_device() - %s", ex)
        return False

    def __str__(self) -> str:
        return f"{self.friendly_name} ({self.ieee_address})"

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

    def link_to_zigbee_device(self) -> None:
        """Attempts to match object to a ZigbeeDevice, if matched the zigbee_device field is set
        and the object is saved.

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
            self.save()
        except ZigbeeDevice.DoesNotExist:
            pass

    def __str__(self):
        return str(self.topic)


class ZigbeeLog(BaseAbstractModel):
    """Captures metadata from MQTT subscription messages"""

    broker_message = models.ForeignKey(ZigbeeMessage, on_delete=models.CASCADE)
    metadata_type = models.CharField(max_length=100)
    metadata_value = models.JSONField(max_length=100)

    def __str__(self):
        return str(self.broker_message)
