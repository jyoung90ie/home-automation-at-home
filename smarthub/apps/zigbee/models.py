import logging
from django.db import models
from ..devices.models import Device, Q
from ..models import BaseAbstractModel

# Create your models here.

logger = logging.getLogger(__name__)


class ZigbeeDevice(BaseAbstractModel):
    """Captures zigbee device metadata and makes connection to user device"""

    INTERVIEW_TYPE = "device_interview"

    device = models.ForeignKey(model=Device, on_delete=models.CASCADE, null=True)
    friendly_name = models.CharField(max_length=100, blank=True, null=True)
    ieee_address = models.CharField(max_length=100, blank=True, null=True)
    device_description = models.CharField(max_length=100, blank=True, null=True)
    interview_completed = models.BooleanField(default=False)
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    firmware_build_date = models.DateField(blank=True, null=True)

    def get_mqtt_data(self, data, data_key):
        """Get device high-level metadata"""
        if not data:
            logger.info(f"No MQTT metadata could be with with key '{data_key}'")
            return

        return data.get(data_key)

    @classmethod
    def process_metadata(self, metadata):
        """If mqtt data type is an interview then capture metadata for model"""
        message_type = self.get_mqtt_data(metadata, "type")
        if message_type and message_type == self.INTERVIEW_TYPE:
            data = self.get_mqtt_data(metadata, "data")
            ieee_address = data.get("ieee_address")

            if not ieee_address:
                return

            zigbee_device = self.objects.filter(ieee_address=ieee_address)

            if not zigbee_device:
                logger.info(f"Found new device with IEEE Address ='{ieee_address}'")
                return self.create_device(self, metadata)

    @classmethod
    def create_device(self, metadata):
        """Creates new zigbee device based on information provided by MQTT broker"""
        data = self.get_mqtt_data(metadata, "data")

        if not data:
            logger.info(
                f"Could not create new zigbee device as metadata did not contain any data"
            )
            return

        device_data = {}
        device_data["friendly_name"] = (data.get("friendly_name"),)
        device_data["ieee_address"] = (data.get("ieee_address"),)

        definition_data = self.get_mqtt_data(data, "definition")

        if definition_data:
            device_data["device_description"] = definition_data.get("description")
            device_data["model"] = definition_data.get("model")
            device_data["brand"] = data.get("vendor")

        zigbee_device = self.objects.create(**device_data)
        logger.info(
            f"Zigbee device created: friendly_name={device_data['friendly_name']} - ieee_address={device_data['ieee_address']}'"
        )

        self.link_device(zigbee_device)

    @classmethod
    def link_device(self, zigbee_device) -> bool:
        """Attempt to match zigbee device to an entry in Device model"""
        obj = zigbee_device or self
        logger.info(f"Attempting to link zigbee device to user devices...")

        if not obj.device:
            zigbee_device = Device.objects.filter(
                Q(friendly_name=obj.friendly_name) | Q(friendly_name=obj.ieee_address)
            )

            if zigbee_device:
                self.device = zigbee_device
                self.save()
                logger.info(
                    f"Zigbee device (friendly_name={obj.friendly_name}) linked to user device uuid='{obj.device.uuid}'"
                )
                return True

        logger.info(
            f"Could not link device - zigbee device (friendly_name={obj.friendly_name}) is already linked to user device uuid='{obj.device.uuid}'"
        )
        return False


class ZigbeeMessage(BaseAbstractModel):
    """Creates an entry to link an MQTT subscription message to a device and metadata"""

    zigbee_device = models.ForeignKey(model=ZigbeeDevice, on_delete=models.CASCADE)
    raw_message = models.JSONField(null=True)
    source_topic = models.CharField(max_length=255, null=True)


class ZigbeeLog(BaseAbstractModel):
    """Captures metadata from MQTT subscription messages"""

    broker_message = models.ForeignKey(model=ZigbeeMessage)
    metadata_type = models.CharField(max_length=100)
    metadata_value = models.JSONField(max_length=100)
