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
    logger.exception("")

if config.with_console:
    interpreter = "python"
else:
    interpreter = "pythonw"


# Pfade zu relevanten Ordnern
project_path = pathlib.Path(__file__).parent.parent
src_path = pathlib.Path(project_path) / "src"
assets_path = pathlib.Path(project_path) / "assets"
noUpdate = pathlib.Path(project_path) / "noUpdate.txt"
venv1 = project_path / ".venv" / "Scripts" / (interpreter + ".exe")
venv2 = project_path / "venv" / "Scripts" / (interpreter + ".exe")

# Daten für die GitHub API
user_agent = "JustAName3/Jans-TODO-Liste (user of the app)"
base_API_url = "https://api.github.com/"
username = "JustAName3"
repo = "Jans-TODO-Liste"
branch = "master"
header = {
    "User-Agent": user_agent
}

root_endpoint = f"{base_API_url}repos/{username}/{repo}/contents"
src_endpoint = f"{root_endpoint}/src"
assets_endpoint = f"{root_endpoint}/assets"
version_txt_url = "https://raw.githubusercontent.com/JustAName3/Jans-TODO-Liste/refs/heads/master/version.txt"

# Wann das API Limit zurückgestzt wird, Unix epoch Zeit
limit_reset = time.time() # Nicht verwendet



# Custom exceptions
class APILimitReached(Exception):

    def __init__(self, reset):
        super().__init__()
        self.reset = reset

    def __str__(self):
        return "Keine API calls mehr übrig"


class StatusCodeError(Exception):

    def __init__(self, status_code):
        super().__init__()
        self.status_code = status_code

    
    def __str__(self):
        return f"Status code != 200, Status: {self.status_code}"


def parse_dict(response_dict) -> dict:
    """
    Parsed das dict der API response. Enthält dann nur noch "name", "type" und "download_url".
    """
    clean_dict = {
        "name": response_dict["name"],
        "download_url": response_dict["download_url"],
        "type": response_dict["type"]
    }

    return clean_dict


def get_files() -> dict[list[dict[str]]]:
    """
    Holt sich alle Dateien in den Pfaden. Nur Namen, nicht die Dateien selbst!

    :returns: dict, keys = src, assets und root, values = list mit return von parse_dict (dict).
    files = {
        	"src": [{
                "name": str,
                "download_url": str,
                "type": str
                }
            ],
            "assets": [{
                "name": str,
                "download_url": str,
                "type": str
                }
            ],
            "root": [{
                "name": str,
                "download_url": str,
                "type": str
                }
            ] 
    }

    :raises: APILimitReached, StatusCodeError
    """
    files = {
        "src": [],
        "assets": [],
        "root": []
    }

    for endpoint in [(src_endpoint, "src"), (assets_endpoint, "assets"), (root_endpoint, "root")]:
        response = requests.get(url= endpoint[0], headers= header, params= {"ref": branch})
        logger.debug(f"RateLimit-Used: {response.headers["X-RateLimit-Used"]}, GitHub-Request-Id: {response.headers["X-GitHub-Request-Id"]}")

        if int(response.headers["X-RateLimit-Remaining"]) <= 1:
            limit_reset = response.headers["X-RateLimit-Reset"] # Unix epoch Zeit

            raise APILimitReached(reset= limit_reset)
        elif response.status_code != 200:
            raise StatusCodeError(status_code= response.status_code)

        for file in response.json(): # file: dict
            files[endpoint[1]].append(parse_dict(response_dict= file))

    # Entfernt alles was nicht vom Typ "file" ist.
    _temp: dict = files
    for dir_key in _temp:   #dir_key: str, key aus dem dict
        for index, elem in enumerate(_temp[dir_key], 0):   # index: int, elem: dict
            if elem["type"] != "file":
                del files[dir_key][index]
                logger.debug(f"Lösche Eintrag {elem} in files[{dir_key}][{index}]")
    
    # Entfernt "config.yaml" aus den Dateien, Nutzereinstellungen sollen nicht überschrieben werden.
    for index, file in enumerate(_temp["root"]):
        if file["name"] == "config.yaml":
            del files["root"][index]
            

    logger.info("Dateinamen bekommen")
    logger.debug(f"Dateien: {files}")

    return files


def replace_file(path, response: requests.Response, encoding = "utf-8") -> pathlib.Path:
    """
    Löscht alte Dateien und speichert neu.
    content muss ein utf-8 String sein. 

    :returns: pathlib.Path, um den Path später zu überprüfen.
    """
    if path.exists():
        os.remove(path= path)
        logger.info(f"Datei {path} gelöscht")

    mode = "wb+" if ".png" in str(path) or ".ico" in str(path) else "w+"
    encoding = None if mode == "wb+" else encoding
    content = response.text if mode == "w+" else response.content
    logger.debug(f"mode: {mode}, encoding: {encoding}")

    with open(file= path, mode= mode, encoding= encoding) as file:
        file.write(content)
        logger.info(f"Datei {path} gespeichert")

    return path

    
def check_paths(paths: list) -> list | None:
    """
    Überprüft alle paths in paths.

    :returns: list wenn ein oder mehrere nicht existieren (welche dann in der Liste sind) oder None wenn alle existieren.
    """
    non_existent = []
    
    for path in paths:
        if not path.exists():
            non_existent.append(path)
            logger.warning(f"Pfad {path} eistiert nicht")

    if len(non_existent) == 0:
        logger.info("Alle Pfade existieren")
        return None
    else:
        logger.warning(f"{non_existent} existieren nicht")
        return non_existent


def update_available(url= version_txt_url) -> bool:
    """
    Überprüft ob die Version in version.txt die gleiche ist wie in main.py.

    :returns: bool und str, False wenn Versionen gleich sind, True wenn nicht, str == Version in version.txt auf GitHub.

    :raises: StatusCodeError
    """
    response = requests.get(url= url, headers= header)

    if response.status_code != 200:
        raise StatusCodeError(status_code= response.status_code)
    
    if response.text == main.VERSION:
        logger.info(f"Kein Update nötig, lokale Version: {main.VERSION}, GitHub: {response.text}")
        return False, response.text
    else:
        logger.info(f"Neue Version verfügbar: {response.text} (lokal: {main.VERSION})")
        return True, response.text


def restart(app_instance):
    if venv1.exists():
        interpreter = venv1
    elif venv2.exists():
        interpreter = venv2

    path = pathlib.Path(src_path) / "main.py"    
    
    logger.info(f'Restarting {path} with interpreter {interpreter}')
    subprocess.Popen([interpreter, path])
    
    app_instance.quit()
    exit()


def update(app_instance):
    """
    Führt ein Update durch.
    """
    if noUpdate.exists():
        logger.debug("noUpdate.txt existiert, Update abgebrochen")
        return

    # Auf Update überprüfen
    try:
        update, version = update_available()
        if not update:
            return
    except StatusCodeError:
        logger.exception("")
        return  

    try:
        files: dict = get_files()
    except APILimitReached:
        logger.exception("")
    except StatusCodeError:
        logger.exception("")
    
    replaced = []

    for dir_key in files: # dir_key: str, key für files

        for file in files[dir_key]: # file: dict
            
            if dir_key == "src":
                path = src_path
            elif dir_key == "assets":
                path = assets_path
            else:
                path = project_path
            
            response = requests.get(url= file["download_url"], headers= header)

            replaced_file: pathlib.Path = replace_file(path= path / file["name"], response= response)
            replaced.append(replaced_file)

    not_found = check_paths(paths= replaced)
    if not_found is not None:
        logger.critical(f"Nicht alle Dateien gefunden ({not_found})")
    else:
        logger.info(f"Update auf Version {version} durchgeführt")

    logger.info("Starte App neu...")

    restart(app_instance= app_instance)