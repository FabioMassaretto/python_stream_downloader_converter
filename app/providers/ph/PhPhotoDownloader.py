import os
import shutil
import requests
from bs4 import BeautifulSoup
from app.helpers.utils.ApplicationVariables import ApplicationVariables
from app.providers.ph.PhDownloaderBase import PhDownloaderBase
from app.config.LoggerConfig import logging

logger = logging.getLogger(__name__)


class PhPhotoDownloader(PhDownloaderBase):
    __dest_pictures_path__ = ApplicationVariables.get("DEST_PICTURES_PATH")

    def __init__(self):
        super().__init__()

    def download(self, url: str) -> None:
        if "album" in url:
            html = requests.get(url).text
            soup = BeautifulSoup(html, 'html.parser')

            title = soup.title.text

            base_url = url.split("/album")[0]

            children = [f'{base_url}{item.find("a")["href"]}' for item in soup.find("ul", "photosAlbumsListing").children if item != "\n"]

        else:
            children = [url,]

        indx = 1
        for i in children:
            try:
                html = requests.get(i).text
                soup = BeautifulSoup(html, 'html.parser')
            except Exception as e:
                logger.error(e)
                continue

            try:
                img = soup.find("div", "centerImage").find("img")["src"]
            except TypeError:
                img = soup.find("div", "centerImage").find(
                    "video").find("source")["src"]
            except AttributeError as ae:
                logger.error(f"No img could be found! Message: {repr(ae)}")

                continue

            title = soup.title.text
            album = soup.find("div", {"id": "thumbSlider"}).find(
                "h2").text[8:]  # .find("ul")#.children[1]

            if not os.path.isdir(f"{self.__dest_pictures_path__}/{title}"):
                os.makedirs(f"{self.__dest_pictures_path__}/{title}")

            r = requests.get(img, stream=True)
            r.raw.decode_content = True

            abspath = os.path.abspath(f"./{self.__dest_pictures_path__}/{title}/{album} - {
                                    i.split('/')[-1]}.{img.split('.')[-1]}".replace("\\", ""))

            with open(abspath, 'wb') as f:
                shutil.copyfileobj(r.raw, f)

            logger.info(f"[+] Downloaded '{self.__dest_pictures_path__}/{title}/{album} - {i.split('/')[-1]}.{img.split(
                '.')[-1]}', {indx}/{len(children)} - {indx / len(children) * 100:.2f}%   ")

            indx += 1
