import os
import requests
from typing import Dict, Optional

from yeeko_abc_message_models.response import ResponseAbc
from yeeko_abc_message_models.response.models import (
    Message, SectionsMessage, ReplyMessage)

FACEBOOK_API_VERSION = os.getenv('FACEBOOK_API_VERSION', 'v13.0')
try:
    FACEBOOK_SECTIONS_LIMIT = int(os.getenv('FACEBOOK_SECTIONS_LIMIT', 10))
except ValueError:
    FACEBOOK_SECTIONS_LIMIT = 10

try:
    FACEBOOK_SECTIONS_BUTTONS_LIMIT = int(
        os.getenv('FACEBOOK_SECTIONS_BUTTONS_LIMIT', 10))
except ValueError:
    FACEBOOK_SECTIONS_BUTTONS_LIMIT = 10


class MessengerResponse(ResponseAbc):
    base_url: str = f'https://graph.facebook.com/{FACEBOOK_API_VERSION}'

    def _get_parameters(self) -> dict:
        if not hasattr(self, "parameters"):
            self.parameters = {}
        return self.parameters

    def set_parameters(self, parameters: dict):
        self.parameters = parameters

    def _base_data(self, recipient_id: str, message_body: dict) -> dict:
        return {
            "recipient": {"id": recipient_id},
            "message": message_body
        }

    def text_to_data(self, message: str, **kwargs) -> dict:
        if not isinstance(message, str):
            raise ValueError(
                f'Message {message} must be a string, not {type(message)}')
        return self._base_data(self.sender_uid, {"text": message})

    def multimedia_to_data(
        self, url_media: str, media_id: str, media_type: str,
        caption: Optional[str] = None,
        **kwargs
    ) -> dict:
        if media_type not in ["image", "video", "audio", "file"]:
            raise ValueError(f"Invalid media type: {media_type}")
        return self._base_data(self.sender_uid, {
            "attachment": {
                "type": media_type,
                "payload": {"url": url_media, "is_reusable": True}
            }
        })

    def _message_to_data(
            self, message: Message, header_supp_media=False
    ) -> dict:
        data = {"text": message.body}
        if message.footer:
            # Messenger does not support a footer natively
            data["metadata"] = message.footer
        return data

    def few_buttons_to_data(self, message: ReplyMessage) -> dict:
        buttons = [
            {
                "type": "postback",
                "title": button.title,
                "payload": button.payload
            }
            for button in message.get_only_buttons()[:3]
        ]
        return self._base_data(self.sender_uid, {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": message.body,
                    "buttons": buttons
                }
            }
        })

    def sections_to_data(self, message: SectionsMessage) -> dict:

        quick_replies = []
        for section in message.sections:
            for item in section.buttons:
                quick_replies.append({
                    "content_type": "text", "title": item.title,
                    "payload": item.payload
                })
        return self._base_data(
            self.sender_uid,
            {"text": message.body, "quick_replies": quick_replies}
        )

    def many_buttons_to_data(self, message: ReplyMessage) -> dict:

        quick_replies = [
            {
                "content_type": "text",
                "title": button.title,
                "payload": button.payload
            }
            for button in message.get_only_buttons()[:FACEBOOK_SECTIONS_BUTTONS_LIMIT]
        ]
        return self._base_data(
            self.sender_uid,
            {"text": message.body, "quick_replies": quick_replies})

    def get_mid(self, body: Dict | None) -> str | None:
        if not body:
            return None
        messages = body.get("messages") or []
        if not messages:
            return None
        return messages[0].get("mid")

    def send_message(
        self, message_data: dict
    ) -> dict:

        url = f"{self.base_url}/me/messages"
        headers = {
            "Authorization": f"Bearer {self.account_token}",
            "Content-Type": "application/json",
        }
        response = requests.post(url, headers=headers, json=message_data)
        try:
            return response.json()
        except ValueError:
            return {"body": response.text}

    def _send_message(self, message: dict) -> dict:
        # clean following attributes
        _ = message.pop("uuid_list", [])
        _ = message.get("_standard_message", None)

        try:
            return self.send_message(message)
        except Exception as e:
            self.add_error(
                {"method": "send_message",  "message": message}, e=e)
            return {"error": str(e)}
