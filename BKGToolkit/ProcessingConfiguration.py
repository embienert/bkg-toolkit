from typing import Iterable

from BKGToolkit.ProcessingModule import ProcessingModule


class ProcessingConfiguration:
    _modules: list[ProcessingModule] = []

    @property
    def modules(self) -> list[ProcessingModule]:
        if self._modules is None:
            self._modules = []
        return self._modules

    @modules.setter
    def modules(self, value: Iterable[ProcessingModule]):
        self._modules = list(value)

    def __init__(self, *modules: ProcessingModule):
        self._modules = list(modules)
