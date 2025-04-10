import datetime
import logging
import pathlib
import json


logger = logging.getLogger("main.functions")
data_path = pathlib.Path(__file__).parent.parent / "data.json"



# def encode(title, note, status: bool) -> dict:
#     """
#     Nimmt die Daten einer Task und codiert sie in JSON. 

#     :returns: dict 
#     """
#     task = {
#         "title": title,
#         "note": note,
#         "status": status
#     }

#     return json.dumps(task)


def read(path = data_path) -> tuple[list[dict[str, str, bool]], tuple[int, int, int, int, int]]:    # Das ist Quatsch
    """
    Öffnet path und liest Inhalt. 

    :returns: tuple[list[dict[str, str, bool]], tuple[int, int, int, int, int]]
    """
    check_for_data()

    with open(path, "r") as file:
        content = json.load(file)
    
    due_day = content["due_day"]
    data = [task for task in content["data"]]

    return data, due_day


def write(due_day: list, data: list[dict[str, str, bool]], path = data_path):
    """
    Schreibt data in path.
    """
    raw = {
        "data": data,
        "due_day": due_day
    }

    json_str = json.dumps(raw, indent= 4)

    with open(path, "w") as file:
        file.write(json_str)


def get_data(tasks: list) -> list:
    """
    Speichert die Attribute title, note, done, date aller gui.Task Instanzen in tasks.

    :returns: list[dict[str, str, bool, list[int, int, int, int, int]]]
    """
    data = []

    for task in tasks:  # task: gui.Task
        attributes = {
            "title": task.title,
            "note":task.note,
            "done": task.done
        }
        
        date = list_date(date= task.date) if task.date is not None else None
        attributes["date"] = date
        
        data.append(attributes)

    return data


def next_reset_date(due_day: int, time: tuple[int, int]):
    """
    Nimmt die Nummer eines Wochentages (0-6) und die Zeit und gibt das Datum des nächsten Tages.
    time = (Stunde, Minute)

    :returns: datetime.datetime
    """
    today = datetime.datetime.today()
    days: int = due_day - today.weekday()

    if days < 0:
        days += 7

    delta = datetime.timedelta(days= days)
    
    next_due_day = today + delta
    next_due_day = next_due_day.replace(hour= time[0], minute= time[1], second= 0, microsecond= 0)

    if check_time(next_due_day)[0]:
        delta = datetime.timedelta(7)
        next_due_day = next_due_day + delta
        

    return next_due_day


def check_time(reset_day: datetime.datetime):
    """
    Returns True wenn der reset erreicht ist.
    Now ist für den Timer, dann muss das nicht nocheinmal geholt werden.

    """
    now = datetime.datetime.today()

    if reset_day > now:
        return False, now
    elif reset_day <= now:
        return True, now 


def check_for_data(path= data_path):
    """
    Überprüft ob die data.json Datei vorhanden ist, wenn nicht wird eine erstellt. 
    """
    if not path.exists():
        empty = {
            "data": [],
            "due_day": list_date(next_reset_date(due_day= 0, time= (0, 0)))
        }
        empty_json = json.dumps(empty)

        with open(path, "w+") as file:
            file.write(empty_json)

        logger.info(f"Keine data.json vorhanden, neue erstellt ({path})")


def list_date(date: datetime.datetime) -> list:
    l = [
        date.year,
        date.month,
        date.day,
        date.hour,
        date.minute
    ]

    return l


def make_date(data: list) -> datetime.datetime:
    date = datetime.datetime(year= data[0],
                             month= data[1],
                             day= data[2],
                             hour= data[3],
                             minute= data[4],
                             second= 0,
                             microsecond= 0)
    
    return date