from abc import ABC, abstractmethod
from typing import Iterable, Any
import numpy as np

from BKGToolkit.DataSpecification import IOSpecification
from BKGToolkit.Settings import Settings
from BKGToolkit.exceptions import IOValidationError
from BKGToolkit.DataSpecification.validation import IOValidationResult, validate_data


class ProcessingModuleSpecification:
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
    __instance_count: int = 0
    _instance_id: int = 0

    info: ProcessingModuleSpecification = None

    inputs: list[IOSpecification] = None
    outputs: list[IOSpecification] = None

    settings: Settings | None = None

    allow_broadcast: bool = False

    def __init__(self, **settings):
        self._instance_id = ProcessingModule.__instance_count
        ProcessingModule.__instance_count += 1

        _cached_data = None
        _cached_result = None

        self.load_settings(settings)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        assert cls.info is not None, "info must be specified"
        assert cls.inputs is not None, "inputs must be specified"
        assert cls.outputs is not None, "output must be specified"

    def load_settings(self, settings: dict):
        if settings is None:
            return

        if self.__class__.settings is None:
            return

        self.settings = self.__class__.settings.copy()
        self.settings.load(settings)

    def run(self, *inputs: Iterable) -> list[Any] | list[Iterable[Any]]:
        inputs_as_array = [np.array(data) for data in inputs]

        # Validate input data
        try:
            input_validations = self._validate_inputs(*inputs_as_array)
        except Exception as validation_error:
            raise IOValidationError(validation_error)

        processing_mode = max([IOValidationResult.OK, *input_validations])
        if processing_mode == IOValidationResult.OK:
            # Linear
            result = self._process(*inputs_as_array)
        elif processing_mode == IOValidationResult.REQUIRE_ITERATION and self.allow_broadcast:
            result = self._process(*inputs_as_array, is_broadcast=True)
        elif processing_mode == IOValidationResult.REQUIRE_ITERATION:
            # iteration required
            result = self._process_multiple(*inputs_as_array, validations=input_validations)
        else:
            raise IOValidationError("One or more single input validation failed")

        # TODO: Result validation?
        return result

    def _validate_inputs(self, *inputs: np.ndarray) -> list[IOValidationResult]:
        if len(inputs) != len(self.inputs):
            raise IOValidationError(f"Expected {len(self.inputs)} inputs, but got {len(inputs)}")

        input_specification_map = zip(self.inputs, inputs)

        validations = [validate_data(specification, data) for specification, data in input_specification_map]

        # Get inputs that must be iterated
        iterable_inputs = []
        for input_data, validation_result in zip(inputs, validations):
            if validation_result.is_iterable():
                iterable_inputs.append(input_data)

        # Check for size mismatch between iterable inputs
        for idx_a in range(len(iterable_inputs)):
            for idx_b in range(idx_a + 1, len(iterable_inputs)):
                if len(iterable_inputs[idx_a]) != len(iterable_inputs[idx_b]):
                    raise IOValidationError(f"Size mismatch between input {idx_a + 1} and input {idx_b + 1}")

        return validations

    @abstractmethod
    def _process(self, *data: np.ndarray, is_broadcast: bool = False) -> list[Any]:
        """
        Process a single dataset

        :param data: validated ndarray containing input data
        :param is_broadcast: whether the input data requires broadcasting
        :return: processed ndarray
        """

        pass

    def _process_multiple(self, *data: np.ndarray, validations: list[IOValidationResult] = None) -> list[Iterable[Any]]:
        """
        Process multiple datasets. Only required if broadcasting is not possible

        :param data: validated ndarray containing multiple input datasets along the first dimension
        :param validations: list of validation results to determine which arguments must be stacked to enable iteration
        :return: processed ndarrays stacked along the first dimension
        """

        # build args
        args = self._stack_args(*data, validations=validations)

        results = []
        for arg_set in args:
            results.append(self._process(*arg_set))

        return list(zip(*results))

    def _stack_args(self, *args: np.ndarray, validations: list[IOValidationResult] = None) -> list[np.ndarray]:
        if validations is None:
            validations = self._validate_inputs(*args)

        assert len(args) == len(validations), "Number of arguments does not match the number of validations"

        arg_stack = []

        length = max([len(arg) for (arg, validation) in zip(args, validations) if validation.is_iterable()])
        for (arg, validation) in zip(args, validations):
            if validation.is_iterable():
                arg_stack.append(arg)
            else:
                arg_stack.append(np.full((length, *arg.shape), arg))

        return list(zip(*arg_stack))

    @property
    def name(self):
        if self.info and self.info.name.strip():
            return self.info.name
        return self.__class__.__name__

    def __str__(self):
        return f"Module({self._instance_id}, {self.name})"

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self._instance_id)
