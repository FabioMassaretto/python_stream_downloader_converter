

from Helpers.Converters.PydubConverter import PydubConverter


class ConverterFactory:
    def create(self, provider):
        return self.__get_converter_provider__(provider)

    def __get_converter_provider__(self, provider):
        if provider == 'PYDUB':
            return PydubConverter()
        else:
            raise ValueError(provider)