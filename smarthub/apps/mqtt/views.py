import logging

from django.http.response import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic.base import View

from ..devices.models import Device, DeviceState
from ..views import UUIDView
from .defines import MQTT_STATE_COMMAND, MQTT_STATE_TOGGLE_VALUE
from .publish import send_message

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
logging.basicConfig()


class ToggleDeviceState(UUIDView, View):
    """Toggle device state - if off, turn on, and vice-versa. Device must be controllable.

    View only accepts POST requests - this is to prevent user's accessing endpoint in browser and
    overloading device with GET requests."""

    http_method_names = [
        "post",
    ]

    def post(self, request, *args, **kwargs):
        """Handle post request"""

        device_uuid = self.kwargs.pop("duuid", None)
        device = get_object_or_404(Device, user=self.request.user, uuid=device_uuid)

        if device and not device.is_linked():
            raise Http404("The device must be linked to a hardware device")

        mqtt_topic = device.get_linked_device().get().friendly_name

        logger.info("publish topic=%s", mqtt_topic)

        try:
            send_message(
                mqtt_topic=mqtt_topic,
                command=MQTT_STATE_COMMAND,
                command_value=MQTT_STATE_TOGGLE_VALUE,
            )
            logger.info("%s - toggle command sent", __name__)

            response = {
                "status": "success",
                "message": f"{device.friendly_name.title()} has been toggled",
            }

        except Exception as ex:
            logger.info("%s - there was a problem sending toggle command", __name__)
            response = {
                "status": "error",
                "message": f"{device.friendly_name.title()} could not be toggled - check the device settings and try again",
            }

        return JsonResponse(response)


class TriggerDeviceState(UUIDView, View):
    """Trigger a device state in response to an event trigger"""

    http_method_names = [
        "post",
    ]

    def post(self, request, *args, **kwargs):
        """Handle post request"""

        state_uuid = self.kwargs.pop("suuid", None)

        try:
            state = get_object_or_404(
                DeviceState,
                uuid=state_uuid,
                zigbee__device__user=self.request.user,
                # TODO - needs updated to reference any related_query_names from GenericRelations
            )
        except Exception as ex:
            print("Error: ", ex)

        state_name = getattr(state, "name")
        cmd = getattr(state, "command")
        val = getattr(state, "command_value")
        hardware_device = getattr(state, "content_object")

        if not cmd or not val:
            logger.info(
                "invoke_event_response: no command and/or value - cmd: %s - val: %s",
                cmd,
                val,
            )
            return

        mqtt_topic = hardware_device.friendly_name
        user_device_name = hardware_device.device.friendly_name.title()

        logger.info("%s - publish topic = %s", __name__, mqtt_topic)

        try:
            send_message(
                mqtt_topic=mqtt_topic,
                command=cmd,
                command_value=val,
            )
            logger.info("%s - toggle command sent", __name__)

            response = {
                "status": "success",
                "message": f"{user_device_name} state updated with configuration from device state '{state_name.title()}'",
            }

        except Exception as ex:
            logger.info("%s - there was a problem sending trigger command", __name__)
            response = {
                "status": "error",
                "message": f"{user_device_name} state could not be changed - check the device settings and try again",
            }

        print(response)
        return JsonResponse(response)
