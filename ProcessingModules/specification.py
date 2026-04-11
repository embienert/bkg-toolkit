class InputSpecification:
    _dimensions: int | None = None
    _shape: tuple | None = None

    def __init__(self, dimensions: int = None, shape: tuple = None):
        if dimensions is None and shape is None:
            raise ValueError("Either dimensions or shape must be specified")
        if dimensions and shape:
            raise ValueError("Cannot specify dimensions AND shape")

        self._dimensions = dimensions
        self._shape = shape

    @property
    def dimensions(self) -> int | None:
        return self._dimensions

    @property
    def shape(self) -> tuple | None:
        return self._shape


class OutputSpecification:
    _dimensions: int | None = None
    _shape: tuple | None = None

    def __init__(self, dimensions: int = None, shape: tuple = None):
        self._dimensions = dimensions
        self._shape = shape

    @property
    def dimensions(self) -> int | None:
        return self._dimensions

    @property
    def shape(self) -> tuple | None:
        return self._shape


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
