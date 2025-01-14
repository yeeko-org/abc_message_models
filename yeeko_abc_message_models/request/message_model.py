import time

from pydantic import BaseModel
from typing import Optional


class MessageBase(BaseModel):
    message_id: str
    timestamp: int
    context_id: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

    def valid_time_interval(self, is_status=False, raise_exception=True):
        max_time = 60000 if is_status else 30000
        timestamp_server = int(time.time())
        long_time_interval = self.timestamp > timestamp_server + max_time

        if long_time_interval and raise_exception:
            raise Exception("YA TE PASASTE, ES MUCHO TIEMPO")
        return long_time_interval


class TextMessage(MessageBase):
    text: str


class InteractiveMessage(MessageBase):
    payload: str
    title: Optional[str]


class EventMessage(MessageBase):
    status: str
    emoji: Optional[str]


class MediaMessage(MessageBase):
    media_type: str
    mime_type: str
    sha256: str
    media_id: str

    caption: str | None = None
    filename: str | None = None
    voice: bool | None = None

    origin_name: str | None = None
