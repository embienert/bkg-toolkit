from enum import Enum
from typing import Iterable
import numpy as np

from DataSpecification.IOSpecification import IOSpecification
from .exceptions import InputValidationError


class InputValidationResult(Enum):
    OK = 0
    REQUIRE_ITERATION = 2
    FAILED = 3

    def is_iterable(self):
        return self == InputValidationResult.REQUIRE_ITERATION

    def __gt__(self, other):
        return self.value > other.value

    def __lt__(self, other):
        return self.value < other.value

    def __ge__(self, other):
        return self.value >= other.value

    def __le__(self, other):
        return self.value <= other.value

    def __eq__(self, other):
        if isinstance(other, InputValidationResult):
            return self.value == other.value

        return self.value == other


def validate(input_specification: IOSpecification, data: Iterable):
    assert isinstance(data, Iterable), "input is non-iterable object"

    data_asarray = np.array(data)

    if input_specification.dimensions:
        return _validate_dimensions(input_specification, data_asarray)
    if input_specification.shape:
        return _validate_shape(input_specification, data_asarray)

    raise InputValidationError("Neither dimensions nor shape were specified")


def _validate_dimensions(self, data: np.ndarray) -> InputValidationResult:
    if not self._dimensions:
        return InputValidationResult.OK

    input_dims = data.ndim

    if input_dims == self._dimensions:
        return InputValidationResult.OK
    if input_dims == self._dimensions + 1:
        return InputValidationResult.REQUIRE_ITERATION

    return InputValidationResult.FAILED


def _validate_shape(self, data: np.ndarray) -> InputValidationResult:
    if not self._shape:
        return InputValidationResult.OK

    input_shape = data.shape

    if input_shape == self._shape:
        return InputValidationResult.OK

    is_one_element_subset = input_shape[1:] == self._shape
    if is_one_element_subset:
        return InputValidationResult.REQUIRE_ITERATION

    return InputValidationResult.FAILED
