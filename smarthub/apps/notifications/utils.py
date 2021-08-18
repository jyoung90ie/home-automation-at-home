import json
import logging

from django.contrib.auth import get_user_model

import requests

from . import defines, models

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Pushbullet:
    """Handles all API requests/responses"""

    API_URL = defines.PUSHBULLET_API_BASE_URL
    CONTENT_TYPE = defines.PUSHBULLET_CONTENT_TYPE
    NOTIFICATION_METHOD = models.NotificationMedium.PUSHBULLET

    # API_URL = "https://api.pushbullet.com"
    # CONTENT_TYPE = "application/json"
    # FREE_MONTHLY_REQUESTS = 500

    # HARDCODED_TOKEN = "o.kF7B0WXtIAo2SvMINmYbkWnQq6H3UQEf"

    auth_header = None
    request = None
    User = get_user_model()

    def __init__(self, user) -> None:
        """Check that user has configured pushbullet"""
        try:
            access_token = user.notification_set.objects.get(
                method=self.NOTIFICATION_METHOD
            ).values_list(flat=True)
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
            logger.info("PUSHBULLET authentication successful")
            logger.info(f"response: {response.json()}")
            return True
        else:
            logger.info("PUSHBULLET authentication failed")
            return False

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

        logger.info(
            f"Sending Pushbullet REQUEST = [url={endpoint_url}, json={json_message}"
        )

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
                f"Pushbullet PUSH - could not be sent as data is incomplete [title={title}, body={body}]"
            )
            return False

        message = {"type": _type, "title": title, "body": body}
        json_message = json.dumps(message)

        return self.make_request(endpoint=endpoint, json_message=json_message)


if __name__ == "__main__":
    pb = Pushbullet("test")
    pb.send_push("Test", "Does this work?")
