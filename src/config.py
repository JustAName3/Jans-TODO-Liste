import pathlib
import yaml

config_path = pathlib.Path(__file__).parent.parent / "config.yaml"
_days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


def load_config(path= config_path):
    """
    Liest die config Datei.

    :raises: FileNotFoundError
    """
    if not path.exists():
        raise FileNotFoundError("Keine Config Datei gefunden.")
    
    with open(path, "r") as file:
        config: dict = yaml.safe_load(file.read())

    global due_day
    global due_time
    global with_console
    global timer_refresh
    global timer_refresh_24h

    # Wichtige Vars
    due_day = _days.index(config["reset_tag"])
    due_time = (config["reset_stunde"], config["reset_minute"])
    with_console = config["konsole"]
    timer_refresh = config["timer_refresh"]
    timer_refresh_24h = config["timer_refresh_24h"]
