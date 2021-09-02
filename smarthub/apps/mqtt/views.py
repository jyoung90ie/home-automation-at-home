from http import HTTPStatus
from .defines import MQTT_STATE_COMMAND, MQTT_STATE_TOGGLE_VALUE
from django.http.response import Http404, HttpResponse, JsonResponse
from django.views.generic.base import View
from django.shortcuts import get_object_or_404
from ..views import UUIDView
from ..devices.models import Device
from .publish import send_message
import logging

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

            # response_status_code = HTTPStatus.NO_CONTENT  # success - no content

        except Exception as ex:
            logger.info("%s - there was a problem sending toggle command", __name__)
            response = {
                "status": "error",
                "message": f"{device.friendly_name.title()} could not be toggled - check the device settings and try again",
            }

        return JsonResponse(response)
        # return HttpResponse(status=response_status_code)


class TriggerDeviceState(UUIDView, View):
    """Trigger a device state in response to an event trigger"""

    pass
