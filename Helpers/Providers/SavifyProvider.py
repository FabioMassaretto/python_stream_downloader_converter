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

        print(f"\n\nWARNING: This is an experimental feature.")
        print(f"WARNING: This can take some second/minutes to finish.")
        print(f"INFO: You have to set client_id and client_secret credentials environment for spotify developer https://developer.spotify.com/.")

        s = Savify(api_credentials=api_credentials, path_holder=path_holder, logger=logging)
        s.download(url)