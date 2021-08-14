import logging
from django.db import models
from django.apps import apps
from ..models import BaseAbstractModel

logger = logging.getLogger("mqtt")
logging.basicConfig()


class ZigbeeDevice(BaseAbstractModel):
    """Captures zigbee device metadata and makes connection to user device"""

    INTERVIEW_TYPE = "device_interview"
    # data to capture from mqtt
    DATA_FIELDS = ["friendly_name", "ieee_address", "model_id", "power_source"]
    DEFINITION_DATA_FIELDS = ["description", "model", "vendor"]

    user_device_model = None

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
    def process_metadata(self, metadata):
        """If mqtt data type is an interview then capture metadata for model"""
        message_type = metadata.get("type")
        if message_type and message_type == self.INTERVIEW_TYPE:
            data = metadata.get("data")
            ieee_address = data.get("ieee_address")

            if not ieee_address:
                return

            zigbee_device: "ZigbeeDevice" = self.objects.filter(
                ieee_address=ieee_address
            )

            if not zigbee_device:
                logger.info(f"Found new device with IEEE Address ='{ieee_address}'")
                return self.create_device(metadata)

    @staticmethod
    def dict_generator(fields, data, dict={}):
        """Returns a dict containing specified data fields"""
        for field in fields:
            dict[field] = data.get(field)

        return dict

    @classmethod
    def create_device(self, metadata):
        """Creates new zigbee device based on information provided by MQTT broker"""
        logger.info(f"ZigbeeDevice metadata={metadata}")

        if not metadata:
            logger.info(
                f"Could not create new zigbee device as metadata did not contain any data"
            )
            return

        device_dict = self.dict_generator(self.DATA_FIELDS, metadata)
        logger.info(f"device dict1: {device_dict}")

        definition_data = metadata.get("definition")

        if definition_data:
            device_dict = self.dict_generator(
                self.DEFINITION_DATA_FIELDS, definition_data, device_dict
            )
            logger.info(f"device dict2: {device_dict}")

        logger.info(f"device dict3: {device_dict}")
        zigbee_device = self.objects.create(**device_dict)
        if zigbee_device:
            logger.info(
                f"Zigbee device created: friendly_name={device_dict['friendly_name']} - ieee_address={device_dict['ieee_address']}'"
            )

            self.link_to_user_device(zigbee_device)
            return zigbee_device

        logger.error(f"Could not create ZigbeeDevice for {device_dict}")
        return None

    @classmethod
    def link_to_user_device(self, zigbee_device=None) -> bool:
        """Attempt to match zigbee device to an entry in Device model"""
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
                    f"Zigbee device (friendly_name={obj.friendly_name}) linked to user device uuid='{obj.device.uuid}'"
                )
                return True
            else:
                logger.info(
                    f"Could not link device (friendly_name={obj.friendly_name}) as no user device exists"
                )
        return False

    def __str__(self) -> str:
        return f"{self.friendly_name} ({self.ieee_address})"


class ZigbeeMessage(BaseAbstractModel):
    """Creates an entry to link an MQTT subscription message to a device and metadata"""

    zigbee_device = models.ForeignKey(
        ZigbeeDevice, on_delete=models.CASCADE, null=True, blank=True
    )
    raw_message = models.JSONField()
    topic = models.CharField(max_length=255)

    def link_to_device_using_topic(self):
        """Updates device for ZigbeeMessage using topic to match to ZigbeeDevice friendly_name - saves if matched"""
        friendly_name_pos = self.topic.rfind("/") + 1
        friendly_name = self.topic[friendly_name_pos:].strip()

        try:
            self.zigbee_device = ZigbeeDevice.objects.get(friendly_name=friendly_name)
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
