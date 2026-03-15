from abc import ABC, abstractmethod
from enum import Enum
from typing import Iterable

import numpy as np

from ProcessingModules.exceptions import InputValidationError


class InputValidationResult(Enum):
    OK = 0
    BROADCAST = 1
    REQUIRE_ITERATION = 2
    FAILED = 3

    def is_iterable(self):
        return self == InputValidationResult.BROADCAST or self == InputValidationResult.REQUIRE_ITERATION


class InputSpecification:
    _dimensions: int | None = None
    _allow_broadcast: bool = False
    _shape: tuple | None = None

    def __init__(self, dimensions: int = None, shape: tuple = None, allow_broadcast: bool = False):
        if dimensions is None and shape is None:
            raise ValueError("Either dimensions or shape must be specified")
        if dimensions and shape:
            raise ValueError("Cannot specify dimensions AND shape")

        self._dimensions = dimensions
        self._shape = shape
        self._allow_broadcast = allow_broadcast


    def validate(self, data: Iterable):
        assert isinstance(data, Iterable), "input is non-iterable object"

        data_asarray = np.array(data)

        if self._dimensions:
            return self._validate_dimensions(data_asarray)
        if self._shape:
            return self._validate_shape(data_asarray)

        raise InputValidationError("Neither dimensions nor shape were specified")


    def _validate_dimensions(self, data: np.ndarray) -> InputValidationResult:
        if not self._dimensions:
            return InputValidationResult.OK

        input_dims = data.ndim

        if input_dims == self._dimensions:
            return InputValidationResult.OK
        if input_dims == self._dimensions + 1 and \
                self._allow_broadcast:
            return InputValidationResult.BROADCAST
        if input_dims == self._dimensions + 1 and \
                not self._allow_broadcast:
            return InputValidationResult.REQUIRE_ITERATION

        return InputValidationResult.FAILED


    def _validate_shape(self, data: np.ndarray) -> InputValidationResult:
        if not self._shape:
            return InputValidationResult.OK

        input_shape = data.shape

        if input_shape == self._shape:
            return InputValidationResult.OK

        is_one_element_subset = input_shape[1:] == self._shape
        if is_one_element_subset and self._allow_broadcast:
            return InputValidationResult.BROADCAST
        if is_one_element_subset and not self._allow_broadcast:
            return InputValidationResult.REQUIRE_ITERATION

        return InputValidationResult.FAILED


class OutputSpecification:
    _dimensions: int | None = None
    _shape: tuple | None = None

    def __init__(self, dimensions: int = None, shape: tuple = None):
        self._dimensions = dimensions
        self._shape = shape


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
        return hash(self.name + self.author)


class ProcessingModule(ABC):
    info: ProcessingModuleInfo = None

    inputs: list[InputSpecification] = None
    output: OutputSpecification = None

    def __init__(self):
        _cached_data = None
        _cached_result = None


    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        assert cls.info is not None, "info must be specified"
        assert cls.inputs is not None, "inputs must be specified"
        assert cls.output is not None, "output must be specified"


    def run(self, *inputs: Iterable) -> np.ndarray:
        inputs_as_array = [np.array(data) for data in inputs]

        # Validate input data
        try:
            input_validations = self._validate_inputs(*inputs_as_array)
        except Exception as validation_error:
            raise InputValidationError(validation_error)

        processing_mode = max(*input_validations)
        if processing_mode == 0 or processing_mode == 1:
            # Linear or broadcast
            result = self.process(*inputs_as_array)
        elif processing_mode == 2:
            # iteration required
            result = self.process_multiple(*inputs_as_array, validations=input_validations)
        else:
            raise InputValidationError("One or more single input validation failed")

        # TODO: Result validation?
        return result


    def _validate_inputs(self, *inputs: np.ndarray) -> list[InputValidationResult]:
        input_specification_map = zip(self.inputs, inputs)

        validations = [specification.validate(data) for specification, data in input_specification_map]

        # Get inputs that must be iterated
        iterable_inputs = []
        for input_data, validation_result in zip(inputs, validations):
            if validation_result.is_iterable():
                iterable_inputs.append(input_data)

        # Check for size mismatch between iterable inputs
        for idx_a in range(len(iterable_inputs)):
            for idx_b in range(idx_a + 1, len(iterable_inputs)):
                if len(iterable_inputs[idx_a]) != len(iterable_inputs[idx_b]):
                    raise InputValidationError(f"Size mismatch between input {idx_a+1} and input {idx_b+1}")

        return validations


    @abstractmethod
    def process(self, *data: np.ndarray) -> np.ndarray:
        """
        Process a single dataset

        :param data: validated ndarray containing input data
        :return: processed ndarray
        """

        pass


    @abstractmethod
    def process_multiple(self, *data: np.ndarray, validations: list[InputValidationResult] = None) -> np.ndarray:
        """
        Process multiple datasets. Only required if broadcasting is not possible

        :param data: validated ndarray containing multiple input datasets along the first dimension
        :param validations: list of validation results to determine which arguments must be stacked to enable iteration
        :return: processed ndarrays stacked along the first dimension
        """

        # build args
        args = self._stack_args(*data, validations=validations)

        # TODO: Check for more efficient/elegant implementation

        results = []
        for arg_set in args:
            results.append(self.process(*arg_set))

        return np.array(results)


    @staticmethod
    def _stack_args(*args: np.ndarray, validations: list[InputValidationResult]) -> list[np.ndarray]:
        assert len(args) == len(validations), "Number of arguments does not match the number of validations"

        arg_stack = []

        length = max([len(arg) for (arg, validation) in zip(args, validations) if validation.is_iterable()])
        for (arg, validation) in zip(args, validations):
            if validation.is_iterable():
                arg_stack.append(arg)
            else:
                arg_stack.append(np.full((length, arg.shape), arg))

        return list(zip(*arg_stack))


    @property
    def name(self):
        if self.info and self.info.name.strip():
            return self.info.name
        return self.__class__.__name__


    def __str__(self):
        return f"Module({self.name})"


    def __repr__(self):
        return self.__str__()


    def __hash__(self):
        if self.info:
            return hash(self.info)

        return hash(self.name)
