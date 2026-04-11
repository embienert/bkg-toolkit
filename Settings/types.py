from abc import ABC
from enum import Enum
from typing import Iterable, Optional


class SettingType(Enum):
    STRING = 0
    BOOLEAN = 1
    INTEGER = 2
    FLOAT = 3
    LIST = 4
    SELECTION = 5

    def get_type(self) -> type:
        if self == SettingType.STRING:
            return str
        elif self == SettingType.BOOLEAN:
            return bool
        elif self == SettingType.INTEGER:
            return int
        elif self == SettingType.FLOAT:
            return float
        elif self == SettingType.LIST:
            return list
        return object

    @staticmethod
    def types() -> list[type]:
        return [sType.get_type() for sType in SettingType]


class Setting[T](ABC):
    _value: T
    _default: T
    _settingType: SettingType

    def __init__(self, default: T, value: T | None = None):
        if default is None:
            raise ValueError("default value must not be None.")
        self._default = default

        if value is not None:
            self._value = value
        else:
            self._value = self._default

    @property
    def default(self) -> T:
        return self._default

    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, value: T) -> None:
        self.validate_value(value)

        self._value = value

    def validate_value(self, value: T):
        exp_type = self._settingType.get_type()
        
        if not isinstance(value, exp_type):
            raise TypeError(f"'{value}' is not a valid {exp_type.__name__}")

    def __str__(self):
        return f"Setting({self._settingType.name}, value: {self._value}, default: {self._default})"

    def __repr__(self):
        return self.__str__()


class StringSetting(Setting[str]):
    _settingType = SettingType.STRING


class BoolSetting(Setting[bool]):
    _settingType = SettingType.BOOLEAN


class IntSetting(Setting[int]):
    _settingType = SettingType.INTEGER


class FloatSetting(Setting[float]):
    _settingType = SettingType.FLOAT


class ListSetting[T](Setting[list[T]]):
    _settingType = SettingType.LIST

    def validate_value(self, value: list[T], dtype: Optional[type] = None):
        super().validate_value(value)

        if not dtype:
            return

        for idx, item in enumerate(value):
            if not isinstance(item, dtype):
                raise TypeError(f"Expected list of {dtype}, but item '{item}' at index {idx} is of type {type(item)}.")


class SelectionSetting[T](Setting[T]):
    _settingType = SettingType.SELECTION
    _options: list[T] = []

    def __init__(self, options: Iterable[T], default: T, value: T | None = None):
        super().__init__(default, value)

        self._options = list(options)
        if not self._options:
            self._options = [default]

    def validate_value(self, value: T):
        if value not in self._options:
            raise ValueError(f"{value} is not a valid selection.")