
from app.helpers.utils.ApplicationEnums import ApplicationEnums


class ApplicationVariables():
    def __init__(self) -> None:
        self.path_enums = ApplicationEnums

    def get(key):
        return ApplicationVariables().path_enums[key].value