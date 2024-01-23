from savify import Savify
from savify.utils import PathHolder
import logging
import os
from dotenv import load_dotenv, find_dotenv

from Helpers.Utils.ApplicationVariables import ApplicationVariables


class SavifyProvider:
    load_dotenv(find_dotenv())
    __dest_converted_audio_path__ = ApplicationVariables().get("DEST_CONVERTED_AUDIO_PATH")

    __CLIENT_ID__ = os.environ.get("CLIENT_ID")
    __CLIENT_SECRET__ = os.environ.get("CLIENT_SECRET")

    __path_holder__ = PathHolder(downloads_path=__dest_converted_audio_path__)
    __api_credentials__ = (__CLIENT_ID__, __CLIENT_SECRET__)

    __savify__ = Savify(api_credentials=__api_credentials__, path_holder=__path_holder__, group='%artist%/%album%' ,logger=logging)


    def __init__(self) -> None:
        print(f"\n\nWARNING: This is an experimental feature.")
        print(f"WARNING: This can take some second/minutes to finish.")
        print(f"INFO: You have to set client_id and client_secret credentials environment for spotify developer https://developer.spotify.com/.\n")


    def download(self, url):
        print("\n\nDownloading...\n")
        self.__savify__.download(url)