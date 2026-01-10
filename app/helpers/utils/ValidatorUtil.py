from typing import List
from app.providers.ProvidersEnum import ProvidersEnum


class ValidatorUtil():

    def is_url_valid(urls: List[str]) -> bool:
        """Validate if the given URL is valid.

        Args:
            url (str): The URL to validate.
            provider (ProvidersEnum): The provider to validate against.
        Returns:
            bool: True if the URL is valid, False otherwise.
        """
        if not urls:
            return False
        
        for url in urls:
            if not ValidatorUtil._is_url_valid_for_provider(url):
                return False
        
        return True
            
    def _is_url_valid_for_provider(url: str) -> bool:
        """Check if the URL is valid for any provider.

        Args:
            url (str): The URL to validate.

        Returns:
            bool: True if the URL is valid for any provider, False otherwise.
        """
        if url.startswith("http://www.youtube") or url.startswith("https://www.youtube") or url.startswith("www.youtube"):
            return True
        elif url.startswith("https://open.spotify.com/") or url.startswith("http://www.spotify.com/") or url.startswith("open.spotify.com/"):
            return True
        
        return False