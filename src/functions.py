import json
import datetime


# def encode(title, note, status: bool) -> dict:
#     """
#     Nimmt die Daten einer Task und codeirt sie in JSON. 

#     :returns: dict 
#     """
#     task = {
#         "title": title,
#         "note": note,
#         "status": status
#     }

#     return json.dumps(task)


def read(path) -> list[dict[str, str, bool]]:
    """
    Öffnet path und liest Inhalt. 

    :returns: list[dict[str, str, bool]] 
    """
    with open(path, "r") as file:
        content = json.load(file)

    data = [task for task in content]

    return data


def write(data: list[dict[str, str, bool]], path):
    """
    Schreibt data in path.
    """
    json_str = json.dumps(data, indent= 4)

    with open(path, "w") as file:
        file.write(json_str)


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

    return next_due_day

