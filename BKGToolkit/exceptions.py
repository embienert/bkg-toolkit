class IOValidationError(Exception):
    pass


class ProcessingFlowError(Exception):
    pass


class NotModuleError(Exception):
    pass


class DuplicateModuleError(Exception):
    pass


class ModuleDoesNotExistError(Exception):
    pass


class ConfigurationError(Exception):
    pass
