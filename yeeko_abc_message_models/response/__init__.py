import json

from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Callable, List, Optional

from yeeko_abc_message_models.utils.parameters import replace_parameter

from .models import (
    Message, ReplyMessage, SectionsMessage, MediaMessage)


def exception_handler(func: Callable) -> Callable:
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            self.add_error({"method": func.__name__, }, e=e)

    return wrapper


class ResponseAbc(ABC, BaseModel):
    sender_uid: str
    account_token: str
    message_list: List[dict] = []
    errors: List[dict] = []

    class Config:
        arbitrary_types_allowed = True

    @abstractmethod
    def _get_parameters(self) -> dict:
        raise NotImplementedError

    def _rep_text(self, text: str) -> str:
        return replace_parameter(
            self._get_parameters(),
            text
        )

    def message_text(self, message: str, fragment_id: Optional[int] = None):
        message = self._rep_text(message)
        message_data = self.text_to_data(message, fragment_id=fragment_id)

        message_data["_standard_message"] = json.loads(
            Message(body=message).model_dump_json())
        self.message_list.append(message_data)

    def message_multimedia(
        self, media_type: str, url_media: str = "", media_id: str = "", caption: str = "",
        fragment_id: Optional[int] = None
    ):
        caption = self._rep_text(caption)
        message_data = self.multimedia_to_data(
            url_media, media_id, media_type, caption, fragment_id=fragment_id)
        message_data["_standard_message"] = json.loads(MediaMessage(
            caption=caption, id=media_id, link=url_media).model_dump_json())
        self.message_list.append(message_data)

    def message_few_buttons(self, message: ReplyMessage):
        message.replace_text(self._get_parameters())

        message_data = self.few_buttons_to_data(message)
        message_data["_standard_message"] = json.loads(
            message.model_dump_json())
        self.message_list.append(message_data)

    def message_many_buttons(self, message: ReplyMessage):
        message.replace_text(self._get_parameters())

        message_data = self.many_buttons_to_data(message)
        message_data["_standard_message"] = json.loads(
            message.model_dump_json())
        self.message_list.append(message_data)

    def message_sections(self, message: SectionsMessage):
        message.replace_text(self._get_parameters())

        message_data = self.sections_to_data(message)
        message_data["_standard_message"] = json.loads(
            message.model_dump_json())
        self.message_list.append(message_data)

    def send_messages(self):
        for message in self.message_list:
            self._send_message(message)

    @abstractmethod
    def _send_message(self, message: dict):
        # pre-clean the message to avoid sending unnecessary data and record events
        raise NotImplementedError

    @abstractmethod
    def text_to_data(
        self, message: str, fragment_id: Optional[int] = None
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def multimedia_to_data(
        self, url_media: str, media_id: str, media_type: str, caption: str,
        fragment_id: Optional[int] = None
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def few_buttons_to_data(self, message: ReplyMessage) -> dict:
        raise NotImplementedError

    @abstractmethod
    def many_buttons_to_data(self, message: ReplyMessage) -> dict:
        raise NotImplementedError

    @abstractmethod
    def sections_to_data(self, message: SectionsMessage) -> dict:
        raise NotImplementedError

    @abstractmethod
    def send_message(
        self, message_data: dict
    ):
        # send the message to the platform
        raise NotImplementedError

    @abstractmethod
    def get_mid(self, body: Optional[dict]) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def add_error(self, error: dict, e: Optional[BaseException] = None):
        raise NotImplementedError
