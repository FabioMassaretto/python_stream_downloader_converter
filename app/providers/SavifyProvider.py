import os
from typing import List
from dotenv import load_dotenv, find_dotenv
from savify.savify import PathHolder, Savify
from app.config.LoggerConfig import logging
from app.helpers.utils.ApplicationVariables import ApplicationVariables

logger = logging.getLogger(__name__)


class SavifyProvider:
    load_dotenv(find_dotenv())

    __dest_converted_audio_path__ = ApplicationVariables.get("DEST_CONVERTED_AUDIO_PATH")

    __CLIENT_ID__ = os.environ.get("CLIENT_ID")
    __CLIENT_SECRET__ = os.environ.get("CLIENT_SECRET")

    __path_holder__ = PathHolder(downloads_path=__dest_converted_audio_path__)
    __api_credentials__ = (__CLIENT_ID__, __CLIENT_SECRET__)

    __savify__ = Savify(api_credentials=__api_credentials__, path_holder=__path_holder__, group='%artist%/%album%', logger=logger)

    def __init__(self) -> None:
        logger.warning("This is an experimental feature.")
        logger.info("You have to set client_id and client_secret credentials environment for spotify developer https://developer.spotify.com/.\n\n")

    # def search(self, query, type: Type = Type.TRACK):
    #     spotify = Spotify(self.__api_credentials__)

    #     result_search = spotify.search(query, type, artist_albums=True)
    #     # result_list.append(result_search)
    #     # result = json.dumps(self.r(result_search.__repr__()), skipkeys=True)
    #     for x in result_search:
    #         logger.info(x)

    def download(self, urls: List[str]):
        logger.info("Downloading... (This can take few seconds/minutes)")

        for url in urls:
            self.__savify__.download(url)
