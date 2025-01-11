from abc import ABC, abstractmethod
from typing import Any, List
from .message_model import (
    InteractiveMessage, EventMessage, MediaMessage, TextMessage
)


class InputSender:
    uid: str
    sender_data: dict
    messages: List[TextMessage | InteractiveMessage |
                   EventMessage | MediaMessage]

    def __init__(self, uid: str, sender_data: dict) -> None:
        self.uid = uid
        self.sender_data = sender_data
        self.messages = []


class InputAccount:
    pid: str
    members: List[InputSender]
    statuses: List[EventMessage]
    raw_data: dict

    account: Any

    def __init__(
        self, raw_data: dict, pid: str
    ) -> None:
        self.raw_data = raw_data
        self.members = []
        self.statuses = []


class RequestAbc(ABC):
    raw_data: dict
    input_accounts: List[InputAccount]

    def __init__(
            self, raw_data: dict
    ) -> None:
        self.raw_data = raw_data
        self.input_accounts = []

        try:
            self.sort_data()
        except Exception as e:
            self.add_error({"method": "sort_data"},  e=e)

    @abstractmethod
    def add_error(self, data: dict, e: Exception):
        raise NotImplementedError

    @abstractmethod
    def sort_data(self):
        raise NotImplementedError

    @abstractmethod
    def data_to_class(
        self, data: dict, pid, token
    ) -> TextMessage | InteractiveMessage | EventMessage | MediaMessage:
        raise NotImplementedError
