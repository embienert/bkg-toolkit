import importlib.util
from pathlib import Path

from BKGToolkit.ProcessingModule import ProcessingModule
from BKGToolkit.exceptions import DuplicateModuleError, ModuleDoesNotExistError, NotModuleError


class ModuleManager:
    _processing_modules: dict[str, type[ProcessingModule]] = {}
    _location: str = "modules"

    @staticmethod
    def register(module: type[ProcessingModule], name: str):
        if not issubclass(module, ProcessingModule):
            raise NotModuleError(f"Only ProcessingModule classes can be registered, but got type {module}")

        if not isinstance(name, str):
            raise ValueError(f"name must be of type str, but got {type(name)}")

        if name in ModuleManager._processing_modules:
            raise DuplicateModuleError(f"Another module with name '{name}' already registered")

        if module in ModuleManager._processing_modules.values():
            raise DuplicateModuleError(f"Module {module} already registered")

        ModuleManager._processing_modules[name] = module

    @staticmethod
    def unregister(module: ProcessingModule = None, name: str = None):
        if module is None and name is None:
            raise ValueError("Either module or name must be specified")

        if module is not None:
            ModuleManager._processing_modules = {
                key: value
                for key, value in ModuleManager._processing_modules.items()
                if value != module
            }
            return

        if name is not None:
            ModuleManager._processing_modules = {
                key: value
                for key, value in ModuleManager._processing_modules.items()
                if key != name
            }

    @staticmethod
    def lookup(name: str):
        if name in ModuleManager._processing_modules:
            return ModuleManager._processing_modules[name]

        raise ModuleDoesNotExistError(f"No module registered with name {name}")

    @staticmethod
    def reverse_lookup(module: type[ProcessingModule]):
        idx = list(ModuleManager._processing_modules.values()).index(module)
        return list(ModuleManager._processing_modules.keys())[idx]

    @staticmethod
    def modules() -> list[type[ProcessingModule]]:
        return list(ModuleManager._processing_modules.values())

    @staticmethod
    def dict() -> dict[str, type[ProcessingModule]]:
        return ModuleManager._processing_modules

    @staticmethod
    def collect():
        module_dir = Path(ModuleManager._location)

        for file in module_dir.glob("*.py"):
            if file.name.startswith("_"):
                continue
            if not file.is_file(follow_symlinks=False):
                continue

            ModuleManager.load_module(file)

    @staticmethod
    def load_module(file: Path):
        spec = importlib.util.spec_from_file_location(file.stem, file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        initializer = getattr(module, "initialize", None)
        if callable(initializer):
            previous_module_count = len(ModuleManager._processing_modules)

            initializer(ModuleManager)

            if len(ModuleManager._processing_modules) == previous_module_count:
                # Change to warning later?
                raise NotModuleError(f"Module {module.__name__} did not register any modules")
        else:
            # initializer function not defined or not callable
            raise NotModuleError(f"Could not find initializer function in module {module.__name__}")

