from savify import Savify
from savify.utils import PathHolder
import logging
import os
from dotenv import load_dotenv, find_dotenv


from Helpers.Utils.ApplicationVariables import ApplicationVariables

class SavifyProvider:
    load_dotenv(find_dotenv())
    dest_converted_audio_path = ApplicationVariables["DEST_CONVERTED_AUDIO_PATH"].value

    def download(self, url):
        CLIENT_ID = os.environ.get("CLIENT_ID")
        CLIENT_SECRET = os.environ.get("CLIENT_SECRET")

        path_holder = PathHolder(downloads_path=self.dest_converted_audio_path)
        api_credentials = (CLIENT_ID, CLIENT_SECRET)

        s = Savify(api_credentials=api_credentials, path_holder=path_holder, logger=logging)
        s.download(url)