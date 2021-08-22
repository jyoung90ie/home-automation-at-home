import json
import logging

import requests

from . import defines

logger = logging.getLogger("mqtt")
logging.basicConfig(level=logging.INFO)


class Pushbullet:
    """Handles all API requests/responses"""

    API_URL = defines.PUSHBULLET_API_BASE_URL
    CONTENT_TYPE = defines.PUSHBULLET_CONTENT_TYPE

    auth_header = None
    request = None

    def __init__(self, access_token: str) -> None:
        """Check that user has configured pushbullet"""
        try:
            # access_token = user.notification_set.objects.get(
            #     method=self.NOTIFICATION_METHOD
            # ).values_list(flat=True)
            # access_token = self.HARDCODED_TOKEN

            self.request = self.authenticate_and_create_auth_header(
                access_token=access_token
            )

        except Exception:
            raise ValueError("User has not configured Pushbullet token")

    def authenticate_and_create_auth_header(
        self, access_token, method: str = "get"
    ) -> bool:
        """Authenticates user token and stores auth header in auth_header instance var"""
        try:
            auth_header = {"Authorization": f"Bearer {str(access_token)}"}

            request = getattr(requests, method.lower())
            response = request(
                self.API_URL,
                headers=auth_header,
            )

            response.raise_for_status()

            logger.info(f"PUSHBULLET auth_response {response}")

            if response.status_code == 200:
                self.auth_header = auth_header
                return True
        except Exception as ex:
            logger.error(ex)

        logger.info("Could not authenticate with pushbullet")

    def make_request(
        self, endpoint: str, json_message: str, method: str = "post"
    ) -> bool:
        """Make the actual API request and handle response"""
        if not self.auth_header:
            logger.info(
                "PUSHBULLET cannot make request until auth_header has been set - has user specified access token?"
            )
            return

        endpoint_url = f"{self.API_URL}{endpoint}"

        headers = self.auth_header
        headers["Content-Type"] = self.CONTENT_TYPE

        request = getattr(requests, method.lower())
        response = request(endpoint_url, headers=headers, data=json_message)

        response.raise_for_status()
        if response.status_code == 200:
            logger.info("PUSHBULLET request successfully processed")
            return response

    def send_push(self, title, body, endpoint="/v2/pushes") -> bool:
        """Setup the 'push' API call and send to make_request"""
        _type = "note"

        if not title or not body:
            logger.info(
                "Pushbullet PUSH - could not be sent as data is incomplete [title=%s, body=%s]",
                title,
                body,
            )
            return False

        message = {"type": _type, "title": title, "body": body}
        json_message = json.dumps(message)

        try:
            return self.make_request(endpoint=endpoint, json_message=json_message)
        except Exception as ex:
            logger.error(ex)
            logger.info("Could not execute Pushbullet send_push(): %s", ex)
