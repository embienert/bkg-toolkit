class IOSpecification:
    _name: str | None = None
    _description: str | None = None

    _dimensions: int | None = None
    _shape: tuple | None = None

    def __init__(self, dimensions: int = None, shape: tuple = None, name: str = None, description: str = None):
        if dimensions is None and shape is None:
            raise ValueError("Either dimensions or shape must be specified")
        if dimensions and shape:
            raise ValueError("Cannot specify dimensions AND shape")

        self._dimensions = dimensions
        self._shape = shape
        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def dimensions(self) -> int | None:
        return self._dimensions

    @property
    def shape(self) -> tuple | None:
        return self._shape
