
from Helpers.Utils.ApplicationEnums import ApplicationEnums


class ApplicationVariables:
    def __init__(self) -> None:
        self.path_enums = ApplicationEnums

    def get(self, key):
        return self.path_enums[key].value