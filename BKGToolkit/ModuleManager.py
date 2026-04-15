from BKGToolkit.ProcessingModule import ProcessingModule


class ModuleManager:
    _processing_modules: dict[str, ProcessingModule] = {}

    @staticmethod
    def register():
        pass
