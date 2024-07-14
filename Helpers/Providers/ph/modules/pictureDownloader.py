import os
import shutil
import requests
from bs4 import BeautifulSoup

from Helpers.Utils.ApplicationVariables import ApplicationVariables

__version__ = "1.0"
__author__ = "FabioMassa"

__dest_pictures_path__ = ApplicationVariables().get("DEST_PICTURES_PATH")
__URL__ = os.environ.get("PH_URL")


def main():

    URL = input(" [?] Album or picture URL: ")
    print("")

    if "album" in URL:
        html = requests.get(URL).text
        soup = BeautifulSoup(html, 'html.parser')

        title = soup.title.text

        children = [f'{__URL__}{i.find("a")["href"]}' for i in soup.find(
            "ul", "photosAlbumsListing").children if i != "\n"]

    else:
        children = [URL,]

    indx = 1
    for i in children:
        try:
            html = requests.get(i).text
            soup = BeautifulSoup(html, 'html.parser')
        except Exception as e:
            print(e)
            continue

        try:
            img = soup.find("div", "centerImage").find("img")["src"]
        except TypeError:
            img = soup.find("div", "centerImage").find(
                "video").find("source")["src"]
        except AttributeError as ae:
            print('Error: No img could be found! Message: ' + ae)
            continue

        title = soup.title.text
        album = soup.find("div", {"id": "thumbSlider"}).find(
            "h2").text[8:]  # .find("ul")#.children[1]

        if not os.path.isdir(f"{__dest_pictures_path__}/{title}"):
            os.makedirs(f"{__dest_pictures_path__}/{title}")

        r = requests.get(img, stream=True)
        r.raw.decode_content = True

        abspath = os.path.abspath(f"./{__dest_pictures_path__}/{title}/{album} - {
                                  i.split('/')[-1]}.{img.split('.')[-1]}".replace("\\", ""))

        with open(abspath, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

        print(f" [+] Downloaded '{__dest_pictures_path__}/{title}/{album} - {i.split('/')[-1]}.{img.split(
            '.')[-1]}', {indx}/{len(children)} - {indx / len(children) * 100:.2f}%   ", end="\r")

        indx += 1

        print("\n\n")
