from typing import Dict, Optional
import os

import requests


from yeeko_abc_message_models.request import (
    InputAccount, InputSender, RequestAbc, SenderData
)
from yeeko_abc_message_models.request.message_model import (
    InteractiveMessage, EventMessage, MediaMessage, MultimediaMessage,
    TextMessage
)

FACEBOOK_API_VERSION = os.getenv('FACEBOOK_API_VERSION', 'v13.0')
FACEBOOK_API_URL = f'https://graph.facebook.com/{FACEBOOK_API_VERSION}'


class IsDeliveryMessage(Exception):
    pass


def set_sender_action(
    sender_id: str,
    token: Optional[str],
    action: str = "mark_seen"
) -> None:
    valid_actions = ["mark_seen", "typing_on", "typing_off"]
    if not all([sender_id, token, action in valid_actions]):
        return

    url = f"{FACEBOOK_API_URL}/me/messages?access_token={token}"

    headers = {
        "Content-Type": "application/json",
    }

    message_data = {
        "recipient": {"id": sender_id},
        "sender_action": "mark_seen"
    }
    _ = requests.post(url, headers=headers, json=message_data)


def get_file_content(media_url: str, token: str) -> bytes | None:
    headers = {
        "Content-Type": "application/json",
    }

    media_response = requests.get(media_url, headers=headers)

    if media_response.status_code == 200:
        return media_response.content


class MessengerRequest(RequestAbc):
    raw_data: dict
    data: dict
    _contacts_data: Dict[str, SenderData]

    messages_ids: list[str]

    def __init__(self, raw_data: dict, debug=False) -> None:
        super().__init__(raw_data, debug=debug)
        self._contacts_data = {}

    def sort_data(self):
        """
            {
                "entry": [
                    {
                        "id": "1228",
                        "messaging": [
                            {
                                "message": {
                                    "mid": "m_qhp",
                                    "text": "test t"
                                },
                                "recipient": {
                                    "id": "1228"
                                },
                                "sender": {
                                    "id": "1653"
                                },
                                "timestamp": 1740393855404
                            }
                        ],
                        "time": 1740393857382
                    }
                ],
                "object": "page"
            }
        """
        entry = self.raw_data.get("entry", [])
        for current_entry in entry:
            try:
                self._process_entry(current_entry)
            except Exception as e:
                data_error = {"entry_data": current_entry}
                self.add_error(data_error, e=e)

    def _process_entry(self, entry_data: dict) -> None:

        input_account = self._get_input_account(entry_data)
        if not input_account:
            return

        self._set_messages(entry_data, input_account)

    def _get_input_account(self, entry_data: dict) -> Optional[InputAccount]:
        pid = entry_data.get("id", {})
        return self.get_input_account(pid, raw_data=entry_data)

    def _set_messages(
        self, entry_data: dict, input_account: InputAccount
    ) -> None:
        """
        {
            "id": "1228", # page id
            "messaging": [
                {
                    "message": {
                        "mid": "m_qhp",
                        "text": "test t"
                    },
                    "recipient": {
                        "id": "1228"
                    },
                    "sender": {
                        "id": "1653"
                    },
                    "timestamp": 1740393855404
                }
            ],
            "time": 1740393857382 # timestamp in epoch
        }
        """
        for message_data in entry_data.get("messaging", []):
            try:
                sender_id = message_data.get("sender", {}).get("id")
            except Exception as e:
                self.add_error({"method": "get_sender_id"}, e=e)
                continue

            try:
                input_sender = input_account.get_input_sender(
                    sender_id, SenderData(raw_data={}))

            except Exception as e:
                data_error = {
                    "method": "get_input_sender",
                    "value.messages.message": message_data
                }
                self.add_error(data_error, e=e)
                continue

            try:
                message_class = self.data_to_class(message_data)
            except IsDeliveryMessage:
                self._set_deliveries(message_data, input_sender)
                continue
            except Exception as e:
                data_error = {
                    "method": "data_to_class",
                    "value.messages.message": message_data
                }
                self.add_error(data_error, e=e)
                continue
            input_sender.messages.append(message_class)

    def data_to_class(
        self, data: dict
    ) -> TextMessage | InteractiveMessage | EventMessage | MediaMessage:

        message_dict_error = ValueError(f"Message data is not a dict {data}")

        # {
        #     "sender": {
        #         "id": "1653"
        #     },
        #     "recipient": {
        #         "id": "1228"
        #     },
        #     "timestamp": 1741606739168,
        #     "read": {
        #         "watermark": 1741606739166
        #     }
        # }

        if "message" in data:
            # posible text, quick_reply or attachments

            if not isinstance(data["message"], dict):
                raise message_dict_error

            if "quick_reply" in data["message"]:
                message = self._create_interactive_message(data)
            elif "attachments" in data["message"]:
                message = self._create_media_message(data)
            else:

                message = self._create_text_message(data)

        elif "postback" in data:
            message = self._create_interactive_message(data)

        elif any([key in data for key in ["read", "reaction"]]):
            message = self._create_state_notification(data)

        elif "delivery" in data:
            raise IsDeliveryMessage

        else:
            raise ValueError(f"Message keys dont support: {data.keys()}")

        if context := data.get("context", {}):
            message.context_id = context.get("id")
        return message

    def _create_text_message(self, data: dict) -> TextMessage:
        """
        {
            "sender": {
                "id": "1653"
            },
            "recipient": {
                "id": "1228"
            },
            "timestamp": 1741604936453,
            "message": {
                "mid": "m_3xrQBZysag-",
                "text": "hi",
                "quick_reply": {
                    "payload": "button_1"
                }
            }
        }
        """
        if not isinstance(message_data := data.get("message"), dict):
            raise ValueError(f"Message data is not a dict {data}")

        text = message_data.get("text", "")
        message_id = message_data.get("mid", "")
        timestamp = data.get("timestamp", 0)
        return TextMessage(
            text=text,
            message_id=message_id,
            timestamp=int(timestamp)
        )

    def _create_interactive_message(self, data: dict) -> InteractiveMessage:
        """
        {
            "sender": {
                "id": "1653"
            },
            "recipient": {
                "id": "1228"
            },
            "timestamp": 1741604936453,
            "message": {
                "mid": "m_3xrQBZysag-",
                "text": "hi",
                "quick_reply": {
                    "payload": "button_1"
                }
            }
        }

        {
            "sender": {
                "id": "1653"
            },
            "recipient": {
                "id": "1228"
            },
            "timestamp": 1741606739127,
            "postback": {
                "title": "Button 3",
                "payload": "button_3",
                "mid": "m_SNFi4_"
            }
        }
        """

        if "message" in data:
            if not isinstance(message_data := data.get("message"), dict):
                raise ValueError(f"Message data is not a dict {data}")

            title = message_data.get("text", "")
            payload = message_data.get("quick_reply", {}).get("payload", "")

        elif "postback" in data:
            if not isinstance(message_data := data.get("postback"), dict):
                raise ValueError(f"Message data is not a dict {data}")

            title = message_data.get("title", "")
            payload = message_data.get("payload", "")

        else:
            raise ValueError(f"Message keys dont support: {data.keys()}")

        message_id = message_data.get("mid", "")
        timestamp = data.get("timestamp", 0)

        return InteractiveMessage(
            message_id=message_id,
            timestamp=int(timestamp),
            title=title,
            payload=payload
        )

    def _create_media_message(self, data: dict) -> MediaMessage:
        """
        {
            "sender": {
                "id": "1653"
            },
            "recipient": {
                "id": "1228"
            },
            "timestamp": 1741606878652,
            "message": {
                "mid": "m_X_k8UWFyj2r",
                "attachments": [
                    {
                        "type": "image",
                        "payload": {
                            "url": "https:\\/\\/scontent.xx."
                        }
                    }
                ]
            }
        }
        """
        if not isinstance(message_data := data.get("message"), dict):
            raise ValueError(f"Message data is not a dict {data}")

        message_id = message_data.get("mid", "")
        timestamp = data.get("timestamp", 0)
        media_type = data.get("type") or "multimedia"

        # TODO: add support for stickers
        multimedia = []

        for attachment in message_data.get("attachments", []):
            if not isinstance(attachment, dict):
                self.add_error(
                    {"attachment_data": attachment},
                    e=ValueError("Attachment data is not a dict")
                )
                continue
            att_media_type = attachment.get("type")
            att_media_url = attachment.get("payload", {}).get("url")
            if not (att_media_type and att_media_url):
                continue

            if not att_media_type in [
                "image", "video", "audio", "document", "sticker"
            ]:
                continue

            try:
                multimedia.append(
                    MultimediaMessage(
                        media_type=att_media_type,
                        media_url=att_media_url
                    )
                )
            except Exception as e:
                self.add_error(
                    {"attachment_data": attachment}, e=e
                )
        if not multimedia:
            self.add_error(
                {"message_data": message_data},
                e=ValueError("No multimedia data supported")
            )

            raise ValueError("No multimedia found")

        return MediaMessage(
            message_id=message_id,
            timestamp=int(timestamp),
            media_type=media_type,
            multimedia=multimedia
        )

    def _create_state_notification(self, status_data: dict) -> EventMessage:
        """
        [
            {
                "sender": {
                    "id": "1653"
                },
                "recipient": {
                    "id": "1228"
                },
                "timestamp": 1741606965521,
                "reaction": {
                    "mid": "m_X_k8UWFyj2r",
                    "action": "react",
                    "emoji": "\\ud83d\\udc4d",
                    "reaction": "like"
                }
            },
            {
                "sender": {
                    "id": "1653"
                },
                "recipient": {
                    "id": "1228"
                },
                "timestamp": 1741606739168,
                "read": {
                    "watermark": 1741606739166
                }
            }
        ]
        """
        emoji = None
        message_id = ""
        status = ""
        timestamp = status_data.get("timestamp") or 0

        if "reaction" in status_data:
            reaction_data: dict = status_data.get("reaction", {})
            message_id = reaction_data.get("mid") or ""
            emoji = reaction_data.get("emoji")
            status = "reaction"
        elif "read" in status_data:
            status = "read"

        return EventMessage(
            message_id=message_id,
            timestamp=timestamp,
            status=status,
            emoji=emoji
        )

    def _set_deliveries(self, status_data: dict, input_sender: InputSender):

        # {
        #     "sender": {
        #         "id": "1653"
        #     },
        #     "recipient": {
        #         "id": "1228"
        #     },
        #     "timestamp": 1741607036752,
        #     "delivery": {
        #         "mids": [
        #             "m_1W3YEmYecuwlkHtMDr"
        #         ],
        #         "watermark": 1741607036471
        #     }
        # }

        timestamp = status_data.get("timestamp") or 0

        if "delivery" in status_data:
            for mid in status_data.get("delivery", {}).get("mids", []):
                status = "delivery"

                delivery_message = EventMessage(
                    message_id=mid,
                    timestamp=timestamp,
                    status=status,
                    emoji=None
                )

                input_sender.messages.append(delivery_message)
