import os
from dotenv import load_dotenv, find_dotenv

from Helpers.Utils import InputUtils
from Helpers.Utils.ApplicationVariables import ApplicationVariables
from modules.savify.logger import Logger
from modules.savify.savify import Savify
from modules.savify.spotify import Spotify
from modules.savify.types import Type
from modules.savify.utils import PathHolder


class SavifyProvider:
    load_dotenv(find_dotenv())
    __dest_converted_audio_path__ = ApplicationVariables().get(
        "DEST_CONVERTED_AUDIO_PATH")

    __CLIENT_ID__ = os.environ.get("CLIENT_ID")
    __CLIENT_SECRET__ = os.environ.get("CLIENT_SECRET")

    __path_holder__ = PathHolder(downloads_path=__dest_converted_audio_path__)
    __api_credentials__ = (__CLIENT_ID__, __CLIENT_SECRET__)

    __logger__ = Logger(log_location='./logs', log_level=20)

    __savify__ = Savify(api_credentials=__api_credentials__,
                        path_holder=__path_holder__, group='%artist%/%album%', logger=__logger__)

    def __init__(self) -> None:
        print(" Chose => Download Spotify audio", end='\n')

        print(f"\n\nWARNING: This is an experimental feature.")
        print(f"INFO: You have to set client_id and client_secret credentials environment for spotify developer https://developer.spotify.com/.", end='\n\n')

        link = InputUtils.handle_user_url_input('spotify')

        if InputUtils.is_digit_and_go_back(link):
            return

        self.download(link)

    def search(self, query, type: Type = Type.ARTIST):
        spotify = Spotify(self.__api_credentials__)

        result_search = spotify.search(query, type, artist_albums=True)
        # result_list.append(result_search)
        # result = json.dumps(self.r(result_search.__repr__()), skipkeys=True)
        for x in result_search:
            print(x)

    def download(self, url):
        print("\n\nDownloading... (This can take few seconds/minutes)\n")
        self.__savify__.download(url)
