from BKGToolkit.DataSpecification.IOSpecification import IOSpecification, IOValidationResult
from BKGToolkit.ProcessingModule import ProcessingModule
from BKGToolkit.exceptions import IOValidationError


class ForwardSpecification:
    src_module: ProcessingModule
    src_output_idx: int
    _src_specification: IOSpecification

    dst_module: ProcessingModule
    dst_input_idx: int
    _dst_specification: IOSpecification

    def __init__(self, from_module: ProcessingModule, from_idx: int, to_module: ProcessingModule, to_idx: int):
        if from_module == to_module:
            raise NotImplementedError("Looped forwarding to the same module is not supported")

        self.src_module = from_module
        self.src_output_idx = from_idx

        self.dst_module = to_module
        self.dst_input_idx = to_idx

    def validate(self) -> IOValidationResult:
        return self.src_specification.validate_specification(self.dst_specification)

    @property
    def src_specification(self) -> IOSpecification:
        if self._src_specification is None:
            src_outputs = self.src_module.outputs

            if src_outputs is None:
                raise IOValidationError("Source module did not specify any outputs")
            if len(src_outputs) <= self.src_output_idx:
                raise IOValidationError("Index out of range for source module outputs")

            self._src_specification = src_outputs[self.src_output_idx]

        return self._src_specification

    @property
    def dst_specification(self) -> IOSpecification:
        if self._dst_specification is None:
            dst_inputs = self.dst_module.inputs

            if dst_inputs is None:
                raise IOValidationError("Destination module did not specify any inputs")
            if len(dst_inputs) <= self.dst_input_idx:
                raise IOValidationError("Index out of range for destination module inputs")

            self._dst_specification = dst_inputs[self.dst_input_idx]

        return self._dst_specification

