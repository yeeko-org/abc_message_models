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
        self.pid = pid
        self.raw_data = raw_data
        self.members = []
        self.statuses = []

    def get_input_sender(
        self, uid: str, sender_data: dict
    ) -> InputSender:
        for member in self.members:
            if member.uid == uid:
                return member

        return self.create_input_sender(uid, sender_data)

    def create_input_sender(
        self, uid: str, sender_data: dict
    ) -> InputSender:
        member = InputSender(uid=uid, sender_data=sender_data)
        self.members.append(member)
        return member


class RequestAbc(ABC):
    raw_data: dict
    input_accounts: List[InputAccount]
    debug: bool = False
    errors: list[dict]

    def __init__(
            self, raw_data: dict, debug: bool = False
    ) -> None:
        self.raw_data = raw_data
        self.input_accounts = []
        self.debug = debug
        self.errors = []

        try:
            self.sort_data()
        except Exception as e:
            self.add_error({"method": "sort_data"},  e=e)

    def add_error(self, data: dict, e: Exception):
        if self.debug:
            print(data)
            raise e
        self.errors.append(data | {"error": str(e)})

    @abstractmethod
    def sort_data(self):
        raise NotImplementedError

    @abstractmethod
    def data_to_class(
        self, data: dict
    ) -> TextMessage | InteractiveMessage | EventMessage | MediaMessage:
        raise NotImplementedError

    def get_input_account(
        self, pid: str, raw_data: dict
    ) -> InputAccount:
        for input_account in self.input_accounts:
            if input_account.pid == pid:
                return input_account

        return self.create_input_account(pid, raw_data)

    def create_input_account(self, pid: str, raw_data: dict) -> InputAccount:
        input_account = InputAccount(raw_data=raw_data, pid=pid)
        self.input_accounts.append(input_account)
        return input_account
