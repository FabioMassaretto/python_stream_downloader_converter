

from Helpers.Converters.PydubConverter import PydubConverter
from config.LoggerConfig import logging

logger = logging.getLogger(__name__)

class ConverterFactory:
    def create(self, provider):
        return self.__get_converter_provider__(provider)

    def __get_converter_provider__(self, provider):
        if provider == 'PYDUB':
            return PydubConverter()
        else:
            logger.error(f"Converter provider '{provider}' is not recognized.")
            
            raise ValueError(provider)