from typing import Iterable
from networkx import DiGraph, is_directed_acyclic_graph, find_cycle, isolates, topological_sort, line_graph

from BKGToolkit.DataSpecification.ForwardSpecification import ForwardSpecification
from BKGToolkit.ProcessingModule import ProcessingModule
from BKGToolkit.exceptions import ProcessingFlowError


class ProcessingNode:
    module: ProcessingModule
    requirements: list[ForwardSpecification]

    def __init__(self, module: ProcessingModule, requirements: list[ForwardSpecification]):
        self.module = module
        self.requirements = requirements


class ProcessingTree:
    _graph: DiGraph[ProcessingNode]
    _sequence: list[ProcessingNode] = None
    _results: dict[ProcessingModule, list] = {}

    @property
    def sequence(self) -> list[ProcessingNode]:
        if self._sequence is None:
            self._sequence = list(topological_sort(self._graph))
        return self._sequence

    @property
    def results(self) -> dict[ProcessingModule, list]:
        """
        Dictionary of all raw result values for each module.

        :return:
        """
        return self._results

    def __init__(self, configuration: ProcessingConfiguration):
        # No validation happens here - Everything in this class assumes that the configuration has been validated
        self.build_processing_tree(configuration)

    @staticmethod
    def cycle_string(cycle: list[tuple[ProcessingModule, ProcessingModule, str]]) -> str:
        cycle_str = ""
        for src, dst, _ in cycle[:-1]:
            cycle_str += f"{src} -> "
        cycle_str += f"{cycle[-1][0]} -> {cycle[-1][1]}"

        return cycle_str

    def build_processing_tree(self, configuration: ProcessingConfiguration):
        graph = DiGraph[ProcessingNode]()

        for module in configuration.modules:
            requirements = [forwarder for forwarder in configuration.forwarders if forwarder.dst_module == module]
            requirements.sort(key=lambda forwarder: forwarder.dst_input_idx)
            graph.add_node(ProcessingNode(module, requirements))

        if not is_directed_acyclic_graph(graph):
            cycle = find_cycle(graph)
            cycle_str = self.cycle_string(cycle)

            raise ProcessingFlowError(f"The processing graph contains a cycle: {cycle_str}")

        # Clean up isolated nodes (there shouldn't be any)
        isolated = list(isolates(graph))
        graph.remove_nodes_from(isolated)

        self._graph = graph

    def execute(self):
        self._results = {}

        for node in self.sequence:
            module = node.module
            requirements = node.requirements

            parameters = []
            for forwarder in requirements:
                parameters.append(self._results[forwarder.src_module][forwarder.src_output_idx])

            results = module.run(*parameters)
            self._results[module] = results


class ProcessingConfiguration:
    _modules: list[ProcessingModule] = []
    _forwarders: list[ForwardSpecification] = []

    @property
    def modules(self) -> list[ProcessingModule]:
        if self._modules is None:
            self._modules = []
        return self._modules

    @modules.setter
    def modules(self, value: Iterable[ProcessingModule]):
        self._modules = list(value)

    @property
    def forwarders(self) -> list[ForwardSpecification]:
        return self._forwarders

    @forwarders.setter
    def forwarders(self, value: Iterable[ForwardSpecification]):
        self._forwarders = list(value)

    def __init__(self, *modules: ProcessingModule):
        self._modules = list(modules)

    def validate(self):
        # Check if all required module inputs are forwarded
        for module in self._modules:
            module_forwarders = [forwarder for forwarder in self._forwarders if forwarder.dst_module == module]
            filled_parameters = [forwarder.dst_input_idx for forwarder in module_forwarders]

            # Check if multiple forwarders point to one parameter
            duplicate_parameters = [parameter for parameter in filled_parameters
                                    if filled_parameters.count(parameter) > 1]
            if duplicate_parameters:
                raise ProcessingFlowError(f"Duplicate ForwardSpecifications for "
                                          f"parameters: {', '.join(map(str, duplicate_parameters))}")

            # Check if any parameters are not being forwarded to
            required_parameters = list(range(len(module.inputs)))
            missing_parameters = [parameter for parameter in required_parameters if parameter not in filled_parameters]
            if missing_parameters:
                raise ProcessingFlowError(f"Missing ForwardSpecifications for "
                                          f"parameters: {', '.join(map(str, missing_parameters))}")

