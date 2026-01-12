from pathlib import Path
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

        for idx, url in enumerate(children, start=1):
            try:
                html = requests.get(url).text
                soup = BeautifulSoup(html, 'html.parser')
            except Exception as e:
                logger.error(e)
                continue

            try:
                img = soup.find("div", "centerImage").find("img")["src"]
            except TypeError:
                img = soup.find("div", "centerImage").find("video").find("source")["src"]
            except AttributeError as ae:
                logger.error(f"No img could be found! Message: {repr(ae)}")

                continue

            title = soup.title.text
            album = soup.find("div", {"id": "thumbSlider"}).find("h2").text[8:]
            
            album_folder: Path = self.__dest_pictures_path__ / title
            album_folder.mkdir(parents=True, exist_ok=True)

            r = requests.get(img, stream=True)
            r.raw.decode_content = True

            image_extension: str = img.split('.')[-1].split("/")[0]
            image_name: str = f"{album} - {url.split('/')[-1]}.{image_extension}"

            image_path: Path = self.__dest_pictures_path__ / title / image_name

            with open(image_path, 'wb') as f:
                shutil.copyfileobj(r.raw, f)

            logger.info(f"[+] Downloaded '{image_name}', {idx}/{len(children)} - {idx / len(children) * 100:.2f}%")
