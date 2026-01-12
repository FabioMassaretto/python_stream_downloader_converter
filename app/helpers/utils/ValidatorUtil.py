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
    
    def is_ph_video_url(url: str) -> bool:
        """Check if the URL is a valid PH video URL.

        Args:
            url (str): The URL to validate.
        Returns:
            bool: True if the URL is a valid PH video URL, False otherwise.
        """
        if url.find("view_video") != -1:
            return True
        
        return False
    
    
    def is_ph_album_url(url: str) -> bool:
        """Check if the URL is a valid PH video URL.

        Args:
            url (str): The URL to validate.
        Returns:
            bool: True if the URL is a valid PH video URL, False otherwise.
        """
        if url.find("album") != -1:
            return True
        
        return False
            

    def _is_url_valid_for_provider(url: str) -> bool:
        """Check if the URL is valid for any provider.

        Args:
            url (str): The URL to validate.

        Returns:
            bool: True if the URL is valid for any provider, False otherwise.
        """
        if url.startswith("https://www.youtube") or url.startswith("www.youtube"):
            return True
        elif url.startswith("https://open.spotify.com/") or url.startswith("https://www.spotify.com/") or url.startswith("open.spotify.com/"):
            return True
        elif url.startswith("https://www.othersite.com/") or url.startswith("www.othersite.com/") or url.startswith("othersite.com/"):
            return True
        
        return False