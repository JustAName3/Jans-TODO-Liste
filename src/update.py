import subprocess
import requests
import logging
import pathlib
import config
import time
import main
import sys
import os

if "log" not in sys.modules:
    import log
logger = logging.getLogger("main.update")

try:
    config.load_config()
except FileNotFoundError:
    logger.exception()


gh_repo = "https://raw.githubusercontent.com/JustAName3/Jans-TODO-Liste/refs/heads/master/"
src_path = pathlib.Path(__file__).parent
assets_path = pathlib.Path(__file__).parent.parent / "assets"
project_path = pathlib.Path(__file__).parent.parent
py_path = pathlib.Path("Scripts", "pythonw.exe")
venv1 = project_path / ".venv" / py_path
venv2 = project_path / "venv" / py_path

noUpdate = pathlib.Path(project_path) / "noUpdate.txt" # Damit beim testen nicht alte Dateien von GitHub heruntergeladen werden.


class VersionException(Exception):

    def __init__(self):
        super().__init__()


    def __str__(self):
        return f"[ERROR] Update nicht nötig"


def parse_updates_txt(text: str):
    lines: list = text.split("\n")
    new_version = lines[0]

    if lines[0] == main.VERSION:
        raise VersionException
    
    del lines[0]
    return lines, new_version


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
            logger.info(f"Deleted {path}")

        with open(path, "wb+") as file:
            file.write(response.content)
            logger.info(f"Saved {path}")

    elif "src" in file:
        path = src_path / file.split("/")[1]

        if path.exists():
            os.remove(path= path)
            logger.info(f"Deleted {path}")

        with open(path, "w+") as file:
            file.write(response.text)
            logger.info(f"Saved {path}")

    elif "tests" in file:   # Vielleicht baue ich noch automatische tests ein
        path = project_path / "tests" / file.split("/")[1]

        if path.exists():
            os.remove(path= path)
            logger.info(f"Deleted {path}")

        with open(path, "w+") as file:
            file.write(response.text)
            logger.info(f"Saved {path}")
    
    else:
        path = project_path / file

        if path.exists():
            os.remove(path= path)
            logger.info(f"Deleted {path}")

        with open(path, "w+") as file:
            file.write(response.text)
            logger.info(f"Saved {path}")


def restart(app_instance):
    if venv1.exists():
        interpreter = venv1
    elif venv2.exists():
        interpreter = venv2
    else:
        if config.with_console:
            interpreter = "python"
        else:
            interpreter = "pythonw"

    path = pathlib.Path(src_path) / "main.py"    
    
    logger.info(f'Restarting {path} with interpreter {interpreter}')
    subprocess.Popen([interpreter, path])
    
    app_instance.quit()
    exit()


def update(app_instance):
    if noUpdate.exists():
        logger.debug("noUpdate exists, cancelled")
        return
    updates = check_for_update()

    try:
        files, new_version = parse_updates_txt(text= updates)
    except VersionException:
        logger.exception()
        return

    for file in files:
        replace_file(file= file)
        time.sleep(1)

    logger.info(f"Update durchgeführt von Version {main.VERSION} zu {new_version}")
    restart(app_instance= app_instance)
