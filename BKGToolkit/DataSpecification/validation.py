from enum import Enum
from typing import Iterable
import numpy as np

from BKGToolkit.DataSpecification import IOSpecification
from BKGToolkit.exceptions import IOValidationError


class IOValidationResult(Enum):
    OK = 0
    REQUIRE_ITERATION = 2
    FAILED = 3

    def is_iterable(self):
        return self == IOValidationResult.REQUIRE_ITERATION

    def __gt__(self, other):
        return self.value > other.value

    def __lt__(self, other):
        return self.value < other.value

    def __ge__(self, other):
        return self.value >= other.value

    def __le__(self, other):
        return self.value <= other.value

    def __eq__(self, other):
        if isinstance(other, IOValidationResult):
            return self.value == other.value

        return self.value == other

    def __ne__(self, other):
        if isinstance(other, IOValidationResult):
            return self.value != other.value

        return self.value != other

    def __and__(self, other):
        if isinstance(other, IOValidationResult):
            return IOValidationResult(max(self.value, other.value))

        return self.value & other


def validate_data(specification: IOSpecification, data: Iterable) -> IOValidationResult:
    assert isinstance(data, Iterable), "input is non-iterable object"

    data_asarray = np.array(data)

    if specification.dimensions:
        return _validate_dimensions(specification, data_asarray.ndim)
    if specification.shape:
        return _validate_shape(specification, data_asarray.shape)

    raise IOValidationError("Neither dimensions nor shape were specified")


def validate_specification(src_specification: IOSpecification,
                           dst_specification: IOSpecification,
                           strict: bool = False) -> IOValidationResult:
    assert isinstance(src_specification, IOSpecification), \
        f"{src_specification} must be of type {IOSpecification.__name__}"
    assert isinstance(dst_specification, IOSpecification), \
        f"{dst_specification} must be of type {IOSpecification.__name__}"

    return (_validate_dimensions(dst_specification, src_specification.dimensions, strict=strict)
            and _validate_shape(dst_specification, src_specification.shape))


def _validate_dimensions(specification: IOSpecification, dimensions: int | None,
                         strict: bool = False) -> IOValidationResult:
    if dimensions is None:
        return IOValidationResult.OK

    if specification.dimensions is not None:
        if dimensions == specification.dimensions:
            return IOValidationResult.OK
        if dimensions == specification.dimensions + 1:
            return IOValidationResult.REQUIRE_ITERATION
    elif specification.shape is not None:
        if strict:
            # cannot guarantee that the output matches the required input shape before runtime
            return IOValidationResult.FAILED
        if dimensions == len(specification.shape):
            return IOValidationResult.OK
        if dimensions == len(specification.shape) + 1:
            return IOValidationResult.REQUIRE_ITERATION

    return IOValidationResult.FAILED


def _validate_shape(specification: IOSpecification, shape: tuple | None) -> IOValidationResult:
    if shape is None:
        return IOValidationResult.OK

    if specification.dimensions is not None:
        if len(shape) == specification.dimensions:
            return IOValidationResult.OK
        if len(shape) == specification.dimensions + 1:
            return IOValidationResult.REQUIRE_ITERATION
    elif specification.shape is not None:
        if shape == specification.shape:
            return IOValidationResult.OK

        is_one_element_subset = shape[1:] == specification.shape
        if is_one_element_subset:
            return IOValidationResult.REQUIRE_ITERATION

    return IOValidationResult.FAILED
