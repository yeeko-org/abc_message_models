from typing import Optional
import os

import requests


from yeeko_abc_message_models.request import InputAccount, RequestAbc
from yeeko_abc_message_models.request.message_model import (
    InteractiveMessage, EventMessage, MediaMessage, TextMessage
)

FACEBOOK_API_VERSION = os.getenv('FACEBOOK_API_VERSION', 'v13.0')
FACEBOOK_API_URL = f'https://graph.facebook.com/{FACEBOOK_API_VERSION}'


def set_status_read(
    message_id: str,
    phone_number_id: str,
    token: Optional[str],
) -> None:
    if not token:
        return

    url = f"{FACEBOOK_API_URL}/{phone_number_id}/messages"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    message_data = {
        "message_id": message_id,
        "messaging_product": "whatsapp",
        "status": "read",
    }
    _ = requests.post(url, headers=headers, json=message_data)


def get_file_content(media_id: str, token: str) -> bytes | None:
    url_media = f"{FACEBOOK_API_URL}/{media_id}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    response = requests.get(url_media, headers=headers)

    if response.status_code == 200:
        media_info = response.json()
        media_url = media_info.get("url")

        media_response = requests.get(media_url, headers=headers)

        if media_response.status_code == 200:
            return media_response.content


class WhatsAppRequest(RequestAbc):
    raw_data: dict
    data: dict
    _contacts_data: dict

    messages_ids: list[str]

    def __init__(self, raw_data: dict, debug=False) -> None:
        super().__init__(raw_data, debug=debug)
        self._contacts_data = {}

    def sort_data(self):
        entry = self.raw_data.get("entry", [])
        for current_entry in entry:

            for change in current_entry.get("changes", []):
                try:
                    self._process_change(change)
                except Exception as e:
                    data_error = {"change_data": change}
                    self.add_error(data_error, e=e)

    def _process_change(self, change: dict) -> None:
        input_account = self._get_input_account(change)
        if not input_account:
            return

        self._full_contact(change)

        self._set_messages(change, input_account)
        self._set_statuses(change, input_account)

    def _get_input_account(self, change: dict) -> Optional[InputAccount]:
        value = change.get("value", {})
        metadata = value.get("metadata", {})
        pid = metadata.get("phone_number_id")

        return self.get_input_account(pid, raw_data=change)

    def _full_contact(self, change: dict) -> None:
        value = change.get("value", {})
        contacts = value.get("contacts", [])
        for contact in contacts:
            # example contact:
            # {
            # "profile": {
            #   "name": "Lucian Vash",
            #   "phone": "5215513375592",
            #   "user_field_filter": "phone"
            # }
            profile = contact.get("profile")
            sender_id = contact.get("wa_id")
            profile["phone"] = contact.get("wa_id")
            profile["user_field_filter"] = "phone"
            self._contacts_data.setdefault(
                sender_id, {
                    "sender_id": sender_id,
                    "contact": profile
                }
            )

    def _set_messages(
        self, change: dict, input_account: InputAccount
    ) -> None:
        value = change.get("value", {})
        messages = value.get("messages", [])
        for message in messages:
            sender_id = message.get("from")
            member_data = self._contacts_data.get(sender_id, {})

            try:
                input_sender = input_account\
                    .get_input_sender(sender_id, member_data)

            except Exception as e:
                data_error = {
                    "method": "get_input_sender",
                    "value.messages.message": message
                }
                self.add_error(data_error, e=e)
                continue

            message_class = self.data_to_class(message)

            input_sender.messages.append(message_class)

    def data_to_class(
        self, data: dict
    ) -> TextMessage | InteractiveMessage | EventMessage | MediaMessage:
        type = data.get("type")
        if type == "text":
            message = self._create_text_message(data)
        elif type == "interactive":
            message = self._create_interactive_message(data)
        elif type in ["state", "reaction"]:
            message = self._create_state_notification(data)
        elif type in ["image", "video", "audio", "document", "sticker"]:
            message = self._create_media_message(data)
        else:
            raise ValueError(f"Message type {type} not supported")

        if context := data.get("context", {}):
            message.context_id = context.get("id")
        return message

    def _create_text_message(self, data: dict) -> TextMessage:
        text = data.get("text", {}).get("body")
        message_id = data.get("id", "")
        timestamp = data.get("timestamp", 0)
        return TextMessage(
            text=text,
            message_id=message_id,
            timestamp=int(timestamp)
        )

    def _create_interactive_message(self, data: dict) -> InteractiveMessage:
        interactive = data.get("interactive", {})
        button_reply: dict = interactive.get(interactive.get("type"), {})
        interactive = InteractiveMessage(
            message_id=data.get("id", ""),
            timestamp=int(data.get("timestamp", 0)),
            title=button_reply.get("title"),
            payload=button_reply.get("id", ""),
        )
        return interactive

    def _create_media_message(self, data: dict) -> MediaMessage:

        message_id = data.get("id", "")
        timestamp = data.get("timestamp", 0)

        media_type = data.get("type")
        if not media_type:
            raise ValueError("Media type not found")
        media_data = data.get(media_type, {})

        mime_type = media_data.get("mime_type")
        sha256 = media_data.get("sha256")
        media_id = media_data.get("id")

        caption = media_data.get("caption")
        filename = media_data.get("filename")
        voice = media_data.get("voice")

        return MediaMessage(
            message_id=message_id,
            timestamp=int(timestamp),
            media_type=media_type,
            mime_type=mime_type,
            sha256=sha256,
            media_id=media_id,
            caption=caption,
            filename=filename,
            voice=voice
        )

    def _create_state_notification(self, status_data: dict) -> EventMessage:
        type_status = status_data.get("type")

        if type_status == "reaction":
            reaction_data: dict = status_data.get("reaction", {})
            message_id = reaction_data.get("message_id") or ""
            emoji = reaction_data.get("emoji")
            status = "reaction"
        else:
            message_id = status_data.get("id") or ""
            status = status_data.get("status") or ""
            emoji = None

        timestamp = status_data.get("timestamp") or 0
        return EventMessage(
            message_id=message_id,
            timestamp=timestamp,
            status=status,
            emoji=emoji
        )

    def _set_statuses(self, change: dict, input_account: InputAccount) -> None:
        value = change.get("value", {})
        statuses = value.get("statuses", [])
        for status_data in statuses:
            sender_id = status_data.get("recipient_id")
            status_data["type"] = "state"
            member_data = self._contacts_data.get(sender_id, {})
            data_error = {"status_data": status_data}

            try:
                input_sender = input_account\
                    .get_input_sender(sender_id, member_data)

            except Exception as e:
                self.add_error(
                    data_error | {"method": "get_input_sender"}, e=e
                )
                continue

            try:

                input_sender.messages.append(
                    self._create_state_notification(status_data)
                )
            except Exception as e:
                self.add_error(
                    data_error | {"method": "create_state_notification"}, e=e
                )
