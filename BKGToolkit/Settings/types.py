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
    FILE = 6

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
    _name: str = ""
    _description: str = ""

    _value: T
    _default: T
    _settingType: SettingType
    _persistent: bool

    def __init__(self, default: T, value: T | None = None, persistent: bool = True,
                 name: str = "", description: str = ""):
        if default is None:
            raise ValueError("default value must not be None.")
        self._default = default

        if value is not None:
            self._value = value
        else:
            self._value = self._default

        self._persistent = persistent
        self._name = name
        self._description = description

    @property
    def default(self) -> T:
        return self._default

    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, value: T) -> None:
        if value is None:
            self._value = self._default
            return

        self.validate_value(value)

        self._value = value

    @property
    def persistent(self) -> bool:
        return self._persistent

    def validate_value(self, value: T):
        exp_type = self._settingType.get_type()
        
        if not isinstance(value, exp_type):
            raise TypeError(f"'{value}' is not a valid {exp_type.__name__}")

    def copy(self):
        return self.__class__(default=self._default, value=self._value)

    def __str__(self):
        return f"Setting({self._settingType.name}, value: {self._value}, default: {self._default})"

    def __repr__(self):
        return self.__str__()

    def __get__(self, instance, owner):
        return self._value

    def __set__(self, instance, value):
        self.value = value


class StringSetting(Setting[str]):
    _settingType = SettingType.STRING


class BoolSetting(Setting[bool]):
    _settingType = SettingType.BOOLEAN
    _enables: list[str] = []

    @property
    def enables(self) -> list[str]:
        return self._enables

    def __init__(self, default: bool, value: bool | None = None, enables: list[str] = None,
                 name: str = "", description: str = ""):
        super().__init__(default, value, name=name, description=description)

        self._enables = enables or []


class IntSetting(Setting[int]):
    _settingType = SettingType.INTEGER


class FloatSetting(Setting[float]):
    _settingType = SettingType.FLOAT


class ListSetting[T](Setting[list[T]]):
    _settingType = SettingType.LIST
    _dtype: type = None

    @property
    def dtype(self) -> type | None:
        return self._dtype

    def __init__(self, default: list[T], value: list[T] = None, dtype: type = None, persistent: bool = True,
                 name: str = "", description: str = ""):
        super().__init__(default, value, persistent, name=name, description=description)
        self._dtype = dtype

    def validate_value(self, value: list[T]):
        super().validate_value(value)

        if not self._dtype:
            return

        for idx, item in enumerate(value):
            if not isinstance(item, self._dtype):
                raise TypeError(f"Expected list of {self._dtype}, but item '{item}' at index {idx} is of type {type(item)}.")


class SelectionSetting[T](Setting[T]):
    _settingType = SettingType.SELECTION
    _options: list[T] = []

    @property
    def options(self) -> list[T]:
        return self._options

    def __init__(self, options: Iterable[T], default: T, value: T | None = None, persistent: bool = True,
                 name: str = "", description: str = ""):
        super().__init__(default, value, persistent, name=name, description=description)

        self._options = list(options)
        if not self._options:
            self._options = [default]

    def validate_value(self, value: T):
        if value not in self._options:
            raise ValueError(f"{value} is not a valid selection.")

    def copy(self):
        return self.__class__(options=self._options, default=self._default, value=self._value)


class FilesSetting(Setting[list[str]]):
    _settingType = SettingType.LIST
    _allow_multiple = True

    @property
    def allow_multiple(self) -> bool:
        return self._allow_multiple

    def __init__(self, default: list[str], value=None, allow_multiple: bool = False, persistent: bool = False,
                 name: str = "", description: str = ""):
        if value is None:
            value = []

        super().__init__(default, value, persistent, name=name, description=description)

        self._allow_multiple = allow_multiple
