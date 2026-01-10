from app.providers import ProviderBase
from app.providers.ProvidersEnum import ProvidersEnum
from app.providers.YtDlpProvider import YtDlpProvider
from app.providers.SavifyProvider import SavifyProvider


class ProviderFactory:
    @staticmethod
    def get_provider_instance(provider_name: ProvidersEnum) -> ProviderBase:
        if provider_name == ProvidersEnum.YTDLP.value:
            return YtDlpProvider()
        elif provider_name == ProvidersEnum.SAVIFY.value:
            return SavifyProvider()
        else:
            raise ValueError(f"Unknown provider: {provider_name}")