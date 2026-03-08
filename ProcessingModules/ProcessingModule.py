from abc import ABC, abstractmethod
from enum import Enum
from typing import Iterable

import numpy as np

from ProcessingModules.exceptions import InputValidationError


class DataMode(Enum):
    """
    Data modes wrt. input and output shape

    SINGLE:     1d > 1d
    MULTI:      2d > 2d
    AGGREGATE:  2d > 1d
    """

    SINGLE = 0
    MULTI = 1
    AGGREGATE = 2


class ShapingMode(Enum):
    """
    Shaping modes wrt. accepted input shapes

    STRICT:     Given data must exactly match the expected input dimensions
    SELECTIVE:  If input dimensions exceed expected input dimensions, select first element matching the dimensions
    """

    STRICT = 0
    SELECTIVE = 1


class ProcessingModuleInfo:
    name: str = ""
    description: str = ""
    author: str = ""
    version: str = ""

    def __init__(self, name: str, description: str = "", author: str = "", version: str = ""):
        self.name = name
        self.description = description
        self.author = author
        self.version = version

    def __str__(self):
        return f"ProcessingModuleInfo(name={self.name}, author={self.author}, version={self.version})"

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.name)


class ProcessingModule(ABC):
    info: ProcessingModuleInfo

    _mode: DataMode = DataMode.SINGLE
    _shaping_mode: ShapingMode = ShapingMode.STRICT

    _cached_data: np.ndarray | None
    _cached_result: np.ndarray | None

    def __init__(self,
                 mode: DataMode = DataMode.SINGLE,
                 shaping_mode: ShapingMode = ShapingMode.STRICT):
        self._mode = mode
        self._shaping_mode = shaping_mode

        _cached_data = None
        _cached_result = None

        self.init_settings()
        self.init_logging()


    def init_settings(self, *args, **kwargs):
        pass


    def init_logging(self, *args, **kwargs):
        pass


    def execute(self, data: Iterable) -> np.ndarray:
        # Validate input data
        try:
            data_asarray = self._validate_data(data)
        except Exception as validation_error:
            raise InputValidationError(validation_error)

        self._cached_data = data_asarray
        self._cached_result = self.process(data_asarray)

        # TODO: Result validation?

        return self._cached_result


    @staticmethod
    def _selective_shape(data: np.ndarray, dims: int) -> np.ndarray:
        """
        Select first element along the last n dimensions

        :param data: ndarray containing at least the number of specified dimensions
        :param dims: required number of dimensions
        :return: ndarray with the required number of dimensions
        """

        idx = [0] * (data.ndim - dims)
        return data[*idx]


    def _validate_data(self, data: Iterable) -> np.ndarray:
        assert isinstance(data, Iterable), "input is non-iterable object"

        data_asarray = np.array(data)
        input_dims = data_asarray.ndim

        # Determine required input dimensions
        required_dims = 1
        if self._mode == DataMode.SINGLE:
            required_dims = 1
        elif self._mode == DataMode.MULTI:
            required_dims = 2

        # Validate input shape
        if self._shaping_mode == ShapingMode.STRICT and \
            input_dims != required_dims:
            raise ValueError(f"Got {input_dims} dimensions, but {required_dims} required for mode STRICT.")
        elif self._shaping_mode == ShapingMode.SELECTIVE and \
            input_dims < required_dims:
            raise ValueError(f"Got {input_dims} dimensions, but at least {required_dims} required for mode SELECTIVE.")

        # Return shaped array
        return self._selective_shape(data_asarray, required_dims)


    @abstractmethod
    def process(self, data: np.ndarray) -> np.ndarray:
        pass


    @property
    def name(self):
        if self.info and self.info.name.strip():
            return self.info.name
        return self.__class__.__name__


    @property
    def mode(self):
        return self._mode


    @property
    def shaping_mode(self):
        return self._shaping_mode


    def __str__(self):
        return f"Module({self.name}, mode={self._mode.name}, shaping={self._shaping_mode.name})"


    def __repr__(self):
        return self.__str__()


    def __hash__(self):
        return hash(self.name)
