from pydantic import BaseModel
from typing import List, Optional

from yeeko_abc_message_models.utils.parameters import replace_parameter


class Button(BaseModel):
    title: str
    payload: str
    description: Optional[str] = None


class SectionHeader(BaseModel):
    title: str


class Header(BaseModel):
    type: str
    value: str


class Message(BaseModel):
    body: str
    header: Optional[str | Header] = None
    footer: Optional[str] = None

    def replace_text(self, extra_values_data: dict):
        self.body = replace_parameter(extra_values_data, self.body)

        if self.header:
            if isinstance(self.header, Header):
                self.header.value = replace_parameter(
                    extra_values_data, self.header.value)
            else:
                self.header = replace_parameter(extra_values_data, self.header)

        if self.footer:
            self.footer = replace_parameter(extra_values_data, self.footer)

    def get_context(self):
        return {}


class ReplyMessage(Message):
    buttons: List[Button | SectionHeader] = []
    button_text: str = "Seleccionar ⏬"

    def get_section(
            self, default_title="Opciones", available_button_space=10
    ) -> List["Section"]:
        sections: List["Section"] = []

        actual_section = None

        for button in self.buttons:
            if isinstance(button, SectionHeader):

                if actual_section and actual_section.buttons:
                    sections.append(actual_section)

                actual_section = Section(title=button.title)
            else:

                if not actual_section:
                    actual_section = Section(title=default_title)

                available_button_space -= 1
                actual_section.buttons.append(button)

            if not available_button_space:
                break

        if actual_section:
            sections.append(actual_section)

        return sections

    def has_sections(self) -> bool:
        return any(isinstance(button, SectionHeader) for button in self.buttons)

    def get_only_buttons(self) -> List[Button]:
        return [button for button in self.buttons if isinstance(button, Button)]

    def replace_text(self, extra_values_data: dict):

        super().replace_text(extra_values_data)

        self.button_text = replace_parameter(
            extra_values_data, self.button_text)

        for index, button in enumerate(self.buttons):
            if isinstance(button, Button):
                self.buttons[index].title = replace_parameter(
                    extra_values_data,
                    button.title
                )
                self.buttons[index].description = replace_parameter(  # type: ignore
                    extra_values_data,
                    button.description or ""
                )
            if isinstance(button, SectionHeader):
                self.buttons[index].title = replace_parameter(
                    extra_values_data,
                    button.title
                )


class Section(BaseModel):
    title: str
    buttons: List[Button] = []

    def replace_text(self, extra_values_data: dict):

        self.title = replace_parameter(
            extra_values_data, self.title)

        for index, button in enumerate(self.buttons):
            if isinstance(button, Button):
                self.buttons[index].title = replace_parameter(
                    extra_values_data,
                    button.title
                )
                self.buttons[index].description = replace_parameter(
                    extra_values_data,
                    button.description or ""
                )


class SectionsMessage(Message):
    button_text: str
    sections: List[Section]
    top_element_style: Optional[str] = "compact"

    def replace_text(self, extra_values_data: dict):
        super().replace_text(extra_values_data)

        self.button_text = replace_parameter(
            extra_values_data, self.button_text)

        for index, _ in enumerate(self.sections):
            self.sections[index].replace_text(extra_values_data)


class MediaMessage(BaseModel):
    caption: str | None
    id: str | None
    link: str | None
