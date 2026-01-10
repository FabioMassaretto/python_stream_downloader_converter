from app.providers import ProviderBase
from app.providers.ProvidersEnum import ProvidersEnum
from app.providers.YtDlpProvider import YtDlpProvider
from app.providers.SavifyProvider import SavifyProvider
from app.providers.ph.PhProvider import PhProvider


class ProviderFactory:
    @staticmethod
    def get_provider_instance(provider_name: ProvidersEnum) -> ProviderBase:
        if provider_name == ProvidersEnum.YTDLP.value:
            return YtDlpProvider()
        elif provider_name == ProvidersEnum.SAVIFY.value:
            return SavifyProvider()
        elif provider_name == ProvidersEnum.PH.value:
            return PhProvider()

        raise ValueError(f"Unknown provider: {provider_name}")