from enum import Enum
from typing import Iterable, Any, Callable, Sequence
import numpy as np

from BKGToolkit.exceptions import IOValidationError


class IOValidationResult(Enum):
    OK = 0
    REQUIRE_ITERATION = 2
    FAILED = 3

    def require_iteration(self):
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


class IOSpecification[T]:
    _name: str | None = None
    _description: str | None = None

    _default: T = None

    _validator: Callable[[T], IOValidationResult] = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def default(self) -> T:
        return self._default

    def __init__(self, name: str = "",
                 description: str = "",
                 default: Any = None,
                 validator: Callable[[Any], IOValidationResult] = None):
        self._name = name
        self._description = description
        self._default = default

    def validate_data(self, data: T) -> IOValidationResult:
        if self._validator is not None:
            return self._validator(data)
        return IOValidationResult.OK

    def validate_specification(self, other: IOSpecification[Any]) -> IOValidationResult:
        if not isinstance(other, IOSpecification):
            raise TypeError(f"Expected IOSpecification, got {type(other)}")

        return IOValidationResult.OK

    def prepare(self, value: T):
        return value


class DataIOSpecification(IOSpecification[np.ndarray]):
    _dimensions: int | None = None
    _shape: tuple | None = None

    @property
    def dimensions(self) -> int | None:
        return self._dimensions

    @property
    def shape(self) -> tuple | None:
        return self._shape

    def __init__(self, dimensions: int = None, shape: tuple = None,
                 name: str = "", description: str = "",
                 default: np.ndarray = None,
                 validator: Callable[[np.ndarray], IOValidationResult] = None):
        super().__init__(name, description, default, validator)

        if dimensions is None and shape is None:
            raise ValueError("Either dimensions or shape must be specified")
        if dimensions and shape:
            raise ValueError("Cannot specify dimensions AND shape")

        self._dimensions = dimensions
        self._shape = shape

    def validate_data(self, data: Iterable) -> IOValidationResult:
        assert isinstance(data, Iterable), "input is non-iterable object"

        data_asarray = np.array(data)

        if self.dimensions:
            return self._validate_dimensions(data_asarray.ndim)
        if self.shape:
            return self._validate_shape(data_asarray.shape)

        raise IOValidationError("Neither dimensions nor shape were specified")

    def validate_specification(self,
                               src_specification: IOSpecification,
                               strict: bool = False) -> IOValidationResult:
        assert isinstance(src_specification, IOSpecification), \
            f"{src_specification} must be of type {IOSpecification.__name__}"

        if not isinstance(src_specification, DataIOSpecification):
            return IOValidationResult.FAILED

        return (self._validate_dimensions(self.dimensions, strict=strict)
                and self._validate_shape(self.shape))

    def _validate_dimensions(self, dimensions: int | None,
                             strict: bool = False) -> IOValidationResult:
        if dimensions is None:
            return IOValidationResult.OK

        if self.dimensions is not None:
            if dimensions == self.dimensions:
                return IOValidationResult.OK
            if dimensions == self.dimensions + 1:
                return IOValidationResult.REQUIRE_ITERATION
        elif self.shape is not None:
            if strict:
                # cannot guarantee that the output matches the required input shape before runtime
                return IOValidationResult.FAILED
            if dimensions == len(self.shape):
                return IOValidationResult.OK
            if dimensions == len(self.shape) + 1:
                return IOValidationResult.REQUIRE_ITERATION

        return IOValidationResult.FAILED

    def _validate_shape(self, shape: tuple | None) -> IOValidationResult:
        if shape is None:
            return IOValidationResult.OK

        if self.dimensions is not None:
            if len(shape) == self.dimensions:
                return IOValidationResult.OK
            if len(shape) == self.dimensions + 1:
                return IOValidationResult.REQUIRE_ITERATION
        elif self.shape is not None:
            if shape == self.shape:
                return IOValidationResult.OK

            is_one_element_subset = shape[1:] == self.shape
            if is_one_element_subset:
                return IOValidationResult.REQUIRE_ITERATION

        return IOValidationResult.FAILED

    def prepare(self, value: Sequence) -> np.ndarray:
        return np.array(value)
