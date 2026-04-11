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


    def validate(self, force_single: bool = False) -> int:
        """
        Validate expected and returned dimensions of the individual modules in the configuration

        :return: 'True' if no issues were detected, 'False' otherwise
        """

        if not self._modules:
            return -1

        if force_single:
            accepted_modes = [DataMode.SINGLE]
        else:
            accepted_modes = [DataMode.SINGLE, DataMode.MULTI, DataMode.AGGREGATE]

        for idx, module in enumerate(self._modules):
            acceptable, accepted_modes = self._validate_data_mode(accepted_modes, module.mode)

            if not acceptable:
                return idx

        return -1

    @staticmethod
    def _validate_data_mode(input_modes: list[DataMode], expected_mode: DataMode) -> (bool, list[DataMode]):
        if expected_mode not in input_modes:
            return False, input_modes

        if expected_mode == DataMode.AGGREGATE:
            input_modes.remove(DataMode.AGGREGATE)  # DataMode.AGGREGATE must be in the list on this execution path

            if DataMode.MULTI in input_modes:
                input_modes.remove(DataMode.MULTI)

        return True, input_modes

