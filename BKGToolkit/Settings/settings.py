from typing import Any, Union
from .types import Setting, SettingType
from warnings import warn


_CONSTRUCTION_TYPE = dict[str, Union[Setting[Any], "Settings", "_CONSTRUCTION_TYPE"]]
_VALUE_TYPE = dict[str, Union[*SettingType.types(), "_VALUE_TYPE"]]


class Settings(dict[str, Setting[Any] | "Settings"]):
    __getattr__ = dict.get
    __delattr__ = dict.__delitem__

    def __init__(self, values: _CONSTRUCTION_TYPE = None, **kwargs):
        all_values = {
            **self._unpack(values),
            **self._unpack(kwargs)
        }

        super().__init__(all_values)

    def __setattr__(self, key, value):
        if not isinstance(value, Setting) and not isinstance(value, Settings):
            raise ValueError(f"Settings items must be of type '{Setting.__name__}' or '{Settings.__name__}' object.")

        dict.__setitem__(self, key, value)

    @staticmethod
    def _unpack(values: dict[str, Setting[Any] | "Settings"]) -> dict[str, Setting[Any]]:
        if values is None:
            return {}

        unpacked_values = {}
        for key, value in values.items():
            if isinstance(value, dict):
                unpacked_values[key] = Settings(value)
            elif isinstance(value, Setting):
                unpacked_values[key] = value
            else:
                raise ValueError(f"Encountered unexpected setting type '{type(value)}' while constructing Settings. "
                                 f"Supported types are '{Setting.__name__}' and '{Settings.__name__}'.")

        return unpacked_values

    def load(self, values: _VALUE_TYPE):
        keys = self.keys()

        for key, value in values.items():
            if key not in keys:
                warn(f"Encountered item {key} while loading settings, which was not specified in struct.")

            setting = self.get(key)
            if isinstance(setting, Setting):
                setting.value = value
            elif isinstance(setting, Settings):
                setting.load(value)
            else:
                # Really shouldn't happen, but you know how it is...
                raise ValueError(f"Encountered unexpected setting type '{type(setting)}' with key {key} while loading "
                                 f"settings.")

    def dump(self) -> _VALUE_TYPE:
        output = {}
        for key, value in self.items():
            setting = self.get(key)
            if isinstance(setting, Setting):
                output[key] = setting.value
            elif isinstance(setting, Settings):
                output[key] = setting.dump()

        return output

    @staticmethod
    def prettify_tree(tree: dict, depth: int = 0) -> str:
        output = ""
        for key, value in tree.items():
            prefix = "\t" * depth
            if isinstance(value, dict):
                output += f"{prefix}{key}\n"
                output += Settings.prettify_tree(value, depth+1)
            else:
                output += f"{prefix}{key}: {value}\n"

        return output

    def prettify(self):
        return self.prettify_tree(self)

    def __str__(self):
        return self.prettify()

    def __repr__(self):
        return f"Settings({super().__repr__()})"
