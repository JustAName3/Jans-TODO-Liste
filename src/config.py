import pathlib
import yaml

config_path = pathlib.Path(__file__).parent.parent / "config.yaml"
days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

d_mode_color = "#000000"    #040626
win_color = 0x00000000


def load_config(path= config_path):
    """
    Liest die config Datei.

    :raises: FileNotFoundError
    """
    if not path.exists():
        make_config_file()
        
    if not path.exists():
        raise FileNotFoundError("Keine Config Datei gefunden.")
    
    with open(path, "r") as file:
        config: dict = yaml.safe_load(file.read())

    global due_day
    global due_time
    global with_console
    global timer_refresh
    global timer_refresh_24h
    global reset_tag
    global d_mode
    global bg_color
    global tx_color

    # Wichtige Vars
    reset_tag = config["reset_tag"]
    due_day = days.index(config["reset_tag"])   # int
    due_time = (config["reset_stunde"], config["reset_minute"])
    with_console = config["konsole"]
    timer_refresh = config["timer_refresh"]
    timer_refresh_24h = config["timer_refresh_24h"]
    d_mode = config["d_mode"]
    bg_color = "white" if not d_mode else d_mode_color
    tx_color = "black" if not d_mode else "white"


def make_config_file():
    """
    Erstellt eine yaml Datei "config.yaml" und speichert standard Werte.
    """
    data = {
        "reset_tag": "Freitag",
        "reset_stunde": 20,
        "reset_minute": 0,
        "konsole": False,
        "timer_refresh": 60000,
        "timer_refresh_24h": 1000,
        "d_mode": False
    }

    path = pathlib.Path(__file__).parent / "config.yaml"

    with open(path, "w+") as file:
        file.write(yaml.dump(data= data))