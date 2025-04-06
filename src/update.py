import requests
import logging
import pathlib
import time
import main
import sys
import os

if "log" not in sys.modules:
    import log
logger = logging.getLogger("main.update")


gh_repo = "https://raw.githubusercontent.com/JustAName3/Jans-TODO-Liste/refs/heads/master/"
src_path = pathlib.Path(__file__).parent
assets_path = pathlib.Path(__file__).parent.parent / "assets"
project_path = pathlib.Path(__file__).parent.parent
noUpdate = pathlib.Path(project_path) / "noUpdate.txt" # Damit beim testen nicht alte Dateien von GitHub heruntergeladen werden.

class VersionException(Exception):

    def __init__(self):
        super().__init__()


    def __str__(self):
        return f"[ERROR] Update nicht nötig"


def parse_updates_txt(text: str):
    lines: list = text.split("\n")

    if lines[0] == main.VERSION:
        raise VersionException
    
    del lines[0]
    return lines


def check_for_update(url= gh_repo):
    response = requests.get(url= gh_repo + "/updates.txt")

    return response.text


def replace_file(file, url = gh_repo):
    logger.info(f"Replacing {file}")
    gh = url + file
    logger.debug(f"Download URL: {gh}")

    response = requests.get(url= gh)
    
    if "assets" in file:
        path = assets_path / file.split("/")[1]

        if path.exists():
            os.remove(path= path)
            logger.debug(f"Deleted {path}")

        with open(path, "wb+") as file:
            file.write(response.content)
            logger.debug(f"Saved {path}")

    elif "src" in file:
        path = src_path / file.split("/")[1]

        if path.exists():
            os.remove(path= path)
            logger.debug(f"Deleted {path}")

        with open(path, "w+") as file:
            file.write(response.text)
            logger.debug(f"Saved {path}")



def update():
    if noUpdate.exists():
        logger.debug("noUpdate exists, cancelled")
        return
    updates = check_for_update()

    try:
        files = parse_updates_txt(text= updates)
    except VersionException:
        logger.exception()
        return

    for file in files:
        replace_file(file= file)

    logger.info("Updated all files")


update()

