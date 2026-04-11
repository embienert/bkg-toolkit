from typing import Iterable

from ProcessingModules import ProcessingModuleBase


class ProcessingConfiguration:
    _modules: list[ProcessingModuleBase] = []

    @property
    def modules(self) -> list[ProcessingModuleBase]:
        if self._modules is None:
            self._modules = []
        return self._modules

    @modules.setter
    def modules(self, value: Iterable[ProcessingModuleBase]):
        self._modules = list(value)


    def __init__(self, *modules: ProcessingModuleBase):
        self._modules = list(modules)
