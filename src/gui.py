from tkinter import PhotoImage
from PIL import Image, ImageTk
from tkinter import ttk
import tkinter as tk
import subprocess
import functions
import datetime
import platform
import pathlib
import logging
import config
import update
import ctypes
import main
import yaml



logger = logging.getLogger("main.gui") 
data_path = pathlib.Path(__file__).parent.parent / "data.json" # Pfad zur Datei mit den Daten
assets_path = pathlib.Path(__file__).parent.parent / "assets"


with Image.open(assets_path / "settings.png") as img:
    settings_png = img.resize((25, 25))

with Image.open(assets_path / "settingsLight.png") as img:
    settings_light_png = img.resize((25, 25))


class App(tk.Tk):

    def __init__(self):

        super().__init__()
        config.load_config()

        self.title("Jans TODO Liste")
        self.iconbitmap(assets_path / "done.ico")
        self.geometry("1050x600")
        # self.configure(background= "#040626")

        self.tasks: list = [] # Hier werden alle Task Instanzen gespeichert.
        # self.data: list = [] # Alle Daten der Tasks werden hier gespeichert. VERALTET
        self.due_day = functions.next_reset_date(due_day= config.due_day, time= config.due_time) # Nächster reset
        self.settings_img = ImageTk.PhotoImage(settings_png)
        self.settings_light_img = ImageTk.PhotoImage(settings_light_png)

        
        # self.gh_label = tk.Label(master= self, text= "GitHub: github.com/JustAName3/Jans-TODO-Liste", foreground= "grey")
        # self.gh_label.pack(padx= 10, pady= 5, side= "bottom")
        self.version_label = tk.Label(master= self, text= f"Version: {main.VERSION}", foreground= "grey", font= "TkDefaultFont 7")
        self.version_label.pack(padx= 10, pady= 5, side= "bottom")


        # Knöpfe oben
        self.nav_frame = tk.Frame(master= self)
        self.nav_frame.pack(padx=10, pady= 10, expand= False, fill= "x")

        self.new_button = tk.Button(master= self.nav_frame, text= "Neu", command= self.add_task)
        self.new_button.grid(row= 0, column= 0)

        # self.update_button = tk.Button(master= self.nav_frame, text= "Update", command= lambda: update.update(app_instance= self))
        # self.update_button.grid(row= 0, column= 1, padx= 10, sticky= "w")

        self.timer = tk.Label(master= self.nav_frame, text= "")
        self.timer.grid(row= 0, column= 1, padx= 10)

        self.settings_button = tk.Button(master= self.nav_frame, text= "", image= self.settings_img, command= lambda: Settings(master= self))
        self.nav_frame.columnconfigure(index= 2, weight= 2)
        self.settings_button.grid(row= 0, column= 2, sticky= "e")


        # Frame mit den Tasks
        self.main_frame = tk.Frame(master= self)
        self.main_frame.pack(anchor= "w", fill= "both", expand= True, side= "left")

        self.canvas = tk.Canvas(master= self.main_frame)

        self.inner_frame = tk.Frame(master= self.canvas)
        self.inner_frame.bind("<Configure>", lambda event: self.canvas.configure(scrollregion= self.canvas.bbox("all")))
        self.inner_frame.bind("<MouseWheel>", lambda event: self.scroll(event= event))

        self.canvas_window = self.canvas.create_window((0, 0), window= self.inner_frame)

        self.scroll_style = ttk.Style(self)
        self.scroll_style.theme_use("default")

        self.scrollbar = ttk.Scrollbar(master= self.main_frame, orient="vertical", command= self.canvas.yview, style= "Vertical.TScrollbar")
        self.canvas.configure(yscrollcommand= self.scrollbar.set)
        
        self.scrollbar.pack(side= "right", fill= "y")
        self.canvas.pack(fill= "both", expand= True)
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfig(self.canvas_window, width= event.width))


        if config.d_mode:
            self.toggle_d_mode()


        self.build_menu()
        self.check_reset()
        self.time()

    
    def toggle_d_mode(self):
        bg_color = config.bg_color
        tx_color = config.tx_color

        self.configure(background= bg_color)
        self.nav_frame.configure(background= bg_color)
        self.new_button.configure(background= bg_color, foreground= tx_color, activebackground= bg_color, activeforeground= bg_color)
        self.timer.configure(background= bg_color, foreground= tx_color)
        self.settings_button.configure(background= bg_color, activebackground= bg_color, activeforeground= bg_color)
        self.version_label.configure(background= bg_color, foreground= tx_color)

        self.main_frame.configure(background= bg_color)
        self.canvas.configure(background= bg_color, highlightbackground= bg_color)
        self.inner_frame.configure(background= bg_color)
        self.scroll_style.configure("Vertical.TScrollbar", background= bg_color, throughcolor= bg_color, activebackground= bg_color)

        settings_image = self.settings_img if not config.d_mode else self.settings_light_img
        self.settings_button.configure(image= settings_image)

        # Farbe vom Windows Fenster ändern
        try:
            if platform.system() == "Windows":
                # Kopiert von https://www.youtube.com/watch?v=36PpT4Z22Os
                # KEINE AHNUNG WIE DAS HIER FUNKTIONIERT!
                HWND = ctypes.windll.user32.GetParent(self.winfo_id())
                win_color = 0x00ffffff if not config.d_mode else config.win_color
                # Keine Ahnung was das returned und ob das wirklich der return Code sein soll.
                ret_code = ctypes.windll.dwmapi.DwmSetWindowAttribute(HWND,
                                                                      35,
                                                                      ctypes.byref(ctypes.c_int(win_color)),
                                                                      ctypes.sizeof(ctypes.c_int))
                logger.debug(f"Fenster Farbe geändert (App). Return Code(?): {ret_code}")
            
            else:
                logger.debug("Fenster Farbe nicht geändert (App). OS != Windows")
        except:
            # Keine Ahung welche Exceptions hier entstehen können, lieber alle abfangen.
            logger.exception("Exception durch Fesnter Farbänderung:")


    def reset(self):
        """
        Setzt alle Tasks auf nicht erledigt.
        """
        for task in self.tasks:
            task.done = False
            task.date = None

        self.due_day = functions.next_reset_date(due_day= config.due_day, time= config.due_time)
        self.save_tasks()
        logger.info("Alle Tasks zurückgesetzt")
        
        self.refresh()

    
    def check_reset(self):
        data, saved_date = functions.read()
        saved_date = functions.make_date(data= saved_date)

        if functions.check_time(reset_day= saved_date)[0]:
            logger.info(f"Resetting Tasks, saved_due_day: {saved_date}")   
            self.reset()


    # Veraltet
    # def open_settings(self):
    #     subprocess.run(["notepad", config.config_path])

    #     update.restart(app_instance= self)


    # adds new tasks 
    def add_task(self):
        t = CreateTask(master= self)
    

    def scroll(self, event):
        self.canvas.yview_scroll(int(-event.delta / 60), "units")
    

    def build_menu(self):
        """
        Erstellt Instanzen von Task und packt diese in self.main_inner_frame.
        """
        data = functions.read()[0]
        
        if data is None:
            logger.warning("Keine Daten in data.json")
            return
        
        ind = 0
        for task in data:  # task: dict 
            date = functions.make_date(task.get("date")) if task.get("date") is not None else None

            self.tasks.append(Task(master= self.inner_frame,
                                   title= task["title"],
                                   note= task["note"],
                                   done= task["done"],
                                   date= date,  # Kann None sein
                                   index= ind,
                                   app_instance= self))
            ind += 1

        
        self.inner_frame.columnconfigure(0, weight= 1)
        row = 0
        for task in self.tasks:
            task.grid(row= row, column= 0, pady= 5, padx= 10, sticky= "ew")
            row += 1
        
        self.after(2, lambda: self.canvas.yview_moveto(0))


    def refresh(self):
        """
        Zerstört die Task Instanzen und called build_menu()
        """
        for frame in self.tasks:
            frame.destroy()
        
        self.tasks.clear()

        self.build_menu()

    
    def save_tasks(self):
        """
        Sammelt alle Daten aus den Tasks und speichert sie in data.json
        """
        data = functions.collect_data(tasks= self.tasks)
        day = functions.list_date(date= self.due_day)

        functions.write(due_day= day, data= data)
        logger.info("Daten gespeichert")


    def delete_task(self, task: int):
        """
        Löscht Tasks aus der Liste und refreshed.
        task ist der Index der Task Instanz in self.tasks.
        """
        logger.info("Lösche Task")
        logger.debug(f"Lösche Task {self.tasks[task].title} (note: {self.tasks[task].note}, done: {self.tasks[task].done})")
        
        self.tasks[task].destroy()
        del self.tasks[task] 


        self.save_tasks()
        self.refresh()

    
    def time(self, recursive = True):
        """
        Aktualisiert den Timer rekursiv.
        """
        reset_reached, now = functions.check_time(reset_day= self.due_day)
        delta = self.due_day - now
        total_s = delta.total_seconds()

        days = delta.days
        hours = int((total_s / 3600) % 24)
        minutes = int((total_s / 60) % 60)
        seconds = total_s % 60

        if total_s > 86400: # 24 Stunden
            wait = config.timer_refresh
            self.timer.configure(text= f"{days} Tage {hours} Stunden {minutes} Minuten")
        else:
            wait = config.timer_refresh_24h
            self.timer.configure(text= f"{hours} Stunden {minutes} Minuten {int(seconds)} Sekunden")


        if reset_reached:
            logger.info("Reset erreicht")
            self.reset()
        
        if recursive is True:
            self.after(wait, self.time)



# Bilder für die Knöpfe 
with Image.open(assets_path / "done.png") as img:
    done_png = img.resize((30, 30))
        
with Image.open(assets_path / "notdone.png") as img:
    notdone_png = img.resize((30, 30))


class Task(tk.Frame):

    def __init__(self, master, title, note, index, app_instance, done= False, date= None):
        super().__init__(master)

        self.title = title
        self.note = note
        self.done = done # Wird True wenn erledigt
        self.date: datetime.datetime = date # Wann die Task erledigt wurde
        self.app_instance = app_instance # Instanz der haupt App, damit man leichter die methoden ausführen kann.
        self.context_menu = ContextMenu(master= self)

        self.configure(relief= "raised", borderwidth= 2)
        self.bind("<Configure>", self.update_width)
        self.bind("<MouseWheel>", lambda event: self.app_instance.scroll(event))
        self.bind("<Button-3>", lambda event: self.context_menu.tk_popup(x= event.x_root, y= event.y_root))


        self.index = index # Index der Daten in App.data
        self.done_img = ImageTk.PhotoImage(done_png)
        self.not_done_img = ImageTk.PhotoImage(notdone_png)


        self.done_button = tk.Button(master= self,
                                     relief= "flat",
                                     command= self.toggle_done)
        self.done_button.bind("<MouseWheel>", lambda event: self.app_instance.scroll(event))
        self.done_button.bind("<Button-3>", lambda event: self.context_menu.tk_popup(x= event.x_root, y= event.y_root))
        
        # zuordnen des richtigen Bildes
        if self.done is False:
            self.done_button.configure(image= self.not_done_img)
        else:
            self.done_button.configure(image= self.done_img)

        self.title_label = tk.Label(master= self,
                                    text= self.title,
                                    font= "TkDefaultFont 14 bold",
                                    wraplength= 1000)
        self.title_label.bind("<MouseWheel>", lambda event: self.app_instance.scroll(event))
        self.title_label.bind("<Button-3>", lambda event: self.context_menu.tk_popup(x= event.x_root, y= event.y_root))

        self.note_message = tk.Message(master= self,
                                       text= self.note)
        self.note_message.bind("<MouseWheel>", lambda event: self.app_instance.scroll(event))
        self.note_message.bind("<Button-3>", lambda event: self.context_menu.tk_popup(x= event.x_root, y= event.y_root))

        self.date_str = f"Erledigt am: {self.date.day}.{self.date.month}.{self.date.year} {self.date.hour}:{self.date.minute} Uhr" if self.date is not None else ""  # Wenn self.date nicht None ist wird dieser String benutzt.
        self.date_label = tk.Label(master= self, text= self.date_str, font= "TkDefaultFont 8", foreground= "grey")
        self.date_label.bind("<Button-3>", lambda event: self.context_menu.tk_popup(x= event.x_root, y= event.y_root))

        # platzieren der Widgets
        self.done_button.grid(row= 0, column= 0, padx= 5, pady= 5, rowspan= 2)
        self.title_label.grid(row= 0, column= 1, padx= (0, 10), sticky= "w")
        self.note_message.grid(row= 1, column= 1, padx= (0, 10), sticky= "w")
        
        if self.date is not None:
            self.date_label.grid(row= 2, column= 1, sticky= "nw")

        if config.d_mode:
            self.toggle_d_mode()


    def toggle_done(self, write = True):
        """
        Stellt done auf True und wechselt das Bild.
        Speichert das Datum wann Aufgabe erledigt wurde, stellt self.date und data["date"] auf None wenn nicht mehr erledigt.
        """
        self.done = not self.done
        
        if self.done:
                self.done_button.configure(image= self.done_img)
                
                self.date = datetime.datetime.today()
                self.date_label.configure(text= f"Erledigt am: {self.date.day}.{self.date.month}.{self.date.year} {self.date.hour}:{self.date.minute} Uhr")
                self.date_label.grid(row= 2, column= 1, padx= 5, pady= 5, sticky= "nw")
                # self.app_instance.data[self.index]["date"] = functions.list_date(self.date)
        else:
            self.done_button.configure(image= self.not_done_img)
            
            self.date = None
            self.date_label.grid_remove()
            # self.app_instance.data[self.index]["date"] = self.date # None

        # self.app_instance.data[self.index]["done"] = self.done
        
        if write:
            self.app_instance.save_tasks()

        logger.debug(f"Status Task {self.title}: {self.done}")

    
    def toggle_d_mode(self):
        """
        Configured die Widget Farben neu. 
        """
        bg_color = config.bg_color
        tx_color = config.tx_color

        self.configure(background= bg_color)
        self.done_button.configure(background= bg_color, activebackground= bg_color, activeforeground= bg_color)
        self.title_label.configure(background= bg_color, foreground= tx_color)
        self.note_message.configure(background= bg_color, foreground= tx_color)
        self.date_label.configure(background= bg_color, foreground= tx_color)

        self.context_menu.toggle_d_mode(bg_color, tx_color)


    # Sorgt dafür, dass sich der Text an die Größe anpasst
    def update_width(self, event):
        new = event.width - 60

        self.note_message.configure(width= new)
        self.title_label.configure(wraplength= new)


    def delete(self):
        self.app_instance.delete_task(task= self.index)


class CreateTask(tk.Toplevel):

    def __init__(self, master):
        
        super().__init__(master)
        # master == App

        self.title("Neue Task erstellen"),
        self.iconbitmap(assets_path / "done.ico")


        self.title_label = tk.Label(master= self, text= "Titel:")
        self.title_label.grid(row= 0, column= 0, padx=10, pady= 20)

        self.title_entry = tk.Entry(master= self, width= 100)
        self.title_entry.grid(row= 0, column= 1, pady=20)

        self.note_label = tk.Label(master= self, text= "Notiz:")
        self.note_label.grid(row= 1, column= 0, padx= 10)

        self.note_text = tk.Text(master= self, width= 100, height= 10)
        self.note_text.grid(row= 1, column= 1, padx= (0, 20), pady= (0, 20))

        self.save_button = tk.Button(master= self, text= "Speichern", command= self.save)
        self.save_button.grid(row= 2, column= 0, padx= 10, pady= (10, 20))

        if config.d_mode:
            self.toggle_d_mode()


    def toggle_d_mode(self):
        bg_color = config.bg_color
        tx_color = config.tx_color

        # Farbe vom Windows Fenster ändern
        try:
            if platform.system() == "Windows":
                # Kopiert von https://www.youtube.com/watch?v=36PpT4Z22Os
                # KEINE AHNUNG WIE DAS HIER FUNKTIONIERT!
                HWND = ctypes.windll.user32.GetParent(self.winfo_id())
                win_color = 0x00ffffff if not config.d_mode else config.win_color
                # Keine Ahnung was das returned und ob das wirklich der return Code sein soll.
                ret_code = ctypes.windll.dwmapi.DwmSetWindowAttribute(HWND,
                                                                      35,
                                                                      ctypes.byref(ctypes.c_int(win_color)),
                                                                      ctypes.sizeof(ctypes.c_int))
                logger.debug(f"Fenster Farbe geändert (CreateTask). Return Code(?): {ret_code}")
            
            else:
                logger.debug("Fenster Farbe nicht geändert (CreateTask). OS != Windows")
        except:
            # Keine Ahung welche Exceptions hier entstehen können, lieber alle abfangen.
            logger.exception("Exception durch Fesnter Farbänderung: ")

        self.configure(background= bg_color)
        self.title_label.configure(foreground= tx_color, background= bg_color)
        self.title_entry.configure(background= bg_color, foreground= tx_color, insertbackground= tx_color)
        self.note_label.configure(background= bg_color, foreground= tx_color)
        self.note_text.configure(background= bg_color, foreground= tx_color, insertbackground= tx_color)
        self.save_button.configure(background= bg_color, foreground= tx_color)


    def clear(self):
        self.title_entry.delete(0, "end")
        self.note_text.delete(1.0, "end")


    def save(self):
        """
        Holt den Text aus den Entries, macht eine Task Instanz und übergibt die Daten an den master.
        """
        title = self.title_entry.get()
        note = self.note_text.get(1.0, "end-1c")

        if title == "":
            logger.info("No title given, returning")
            return 

        index = len(self.master.tasks) +1 

        new_task = Task(master= self.master.inner_frame,
                        title= title,
                        note= note,
                        app_instance= self.master,
                        index= index)

        self.master.tasks.append(new_task)

        logger.info("Task hinzugefügt")
        logger.debug(f"Titel: {title}, note: {note}")

        self.master.save_tasks()
        # functions.write(data= self.master.data, due_day= functions.list_date(self.master.due_day))

        self.master.refresh()
        self.clear()


with Image.open(assets_path / "trash.png") as img:
    trash_png = img.resize(size= (15, 15))
with Image.open(assets_path / "edit.png") as img:
    edit_png = img.resize(size= (15, 15))

with Image.open(assets_path / "trashLight.png") as img:
    trash_light_png = img.resize((15, 15))
with Image.open(assets_path / "editLight.png") as img:
    edit_light_png = img.resize((15, 15))


class ContextMenu(tk.Menu):

    def __init__(self, master):
        super().__init__(master)
        # master == Task

        self.configure(tearoff= 0)

        self.trash_png = ImageTk.PhotoImage(trash_png)
        self.edit_png = ImageTk.PhotoImage(edit_png)

        # Bilder für Darkmode
        self.trash_light_img = ImageTk.PhotoImage(trash_light_png)
        self.edit_light_img = ImageTk.PhotoImage(edit_light_png)

        self.add_command(label= "Löschen", image= self.trash_png, compound= "left", command= self.delete)

        self.add_command(label= "Bearbeiten", image= self.edit_png, compound= "left", command= self.edit)

    
    def toggle_d_mode(self, bg_color, tx_color):
        trash_image = self.trash_png if not config.d_mode else self.trash_light_img
        edit_image = self.edit_png if not config.d_mode else self.edit_light_img

        self.configure(background= bg_color, foreground= tx_color)

        self.entryconfigure(index= "Löschen", image= trash_image)
        self.entryconfigure(index= "Bearbeiten", image= edit_image)


    def delete(self):
        self.master.delete()


    def edit(self):
        editor = EditTask(master= self.master)


class EditTask(CreateTask):

    def __init__(self, master):
        super().__init__(master)
        # master == Task

        self.title("Task bearbeiten")
        self.save_button.configure(command= self.save_edit)

        self.title_entry.insert(0, self.master.title)
        self.note_text.insert(0.0, self.master.note)

        # self.index = index # Index von Task Instanz in App.tasks

    
    def save_edit(self):
        new_title = self.title_entry.get()
        new_note = self.note_text.get(1.0, "end-1c")

        if new_title == "":
            logger.info("No title given, returning")
            return 

        self.master.title = new_title
        self.master.note = new_note

        logger.info("Task bearbeitet")
        logger.info(f"Neuer Titel: {self.master.title}, neue note: {self.master.note}")

        self.master.app_instance.save_tasks()
        self.master.app_instance.refresh()
        self.destroy()


class Settings(tk.Toplevel):
    """
    Custom tk.Toplevel für das Einstellungsmenü.
    """
    def __init__(self, master: App):
        # master = App

        super().__init__(master)

        self.title("Einstellungen")
        self.iconbitmap(assets_path / "done.ico")
    
        # tk Vars für die OptionMenus 
        self.day_var = tk.StringVar(self, value= config.reset_tag)
        self.hour_var = tk.IntVar(self, value = config.due_time[0])
        self.minute_var = tk.IntVar(self, value= config.due_time[1])

        self.day_var.trace(mode= "w", callback= self.next_reset_save)
        self.hour_var.trace(mode= "w", callback= self.next_reset_save)
        self.minute_var.trace(mode= "w", callback= self.next_reset_save)


        #tk BooleanVar für den Darkmode Checkbuttton
        self.d_mode_var = tk.BooleanVar(master= self, value= config.d_mode)

        self.d_mode_var.trace(mode= "w", callback= self.d_mode_save)

    
        self.raw_reset_date_str: str = "Nächster Reset am {d}.{mo}.{y} um {h}:{m} Uhr"
        self.reset_day = functions.next_reset_date(due_day= config.days.index(self.day_var.get()), time= (self.hour_var.get(), self.minute_var.get()))


        # Optionen zum einstellen der Reset Zeit
        self.time_options_label = tk.Label(master= self, text= "Reset Zeit:")
        self.time_options_label.pack(padx=10, pady= (10, 0), anchor= "w")

        self.time_frame = tk.Frame(master= self, borderwidth= 2, relief= "raised")
        self.time_frame.pack(padx= 10, pady= (0, 10), fill= "x", expand= True, anchor= "n")

        self.day_option = tk.OptionMenu(self.time_frame, self.day_var, *config.days)
        self.day_option.grid(row= 0, column= 0, pady= 5)

        self.hour_label = tk.Label(master= self.time_frame, text= "Stunde:")
        self.hour_label.grid(row= 0, column= 1, padx= (5, 0), pady= 5)

        self.hour_option = tk.OptionMenu(self.time_frame, self.hour_var, *[i for i in range(0, 24)])
        self.hour_option.grid(row= 0, column= 2, padx= 5, pady= 5)

        self.minute_label = tk.Label(master= self.time_frame, text= "Minute:")
        self.minute_label.grid(row= 0, column= 3, pady= 5)

        self.minute_option = tk.OptionMenu(self.time_frame, self.minute_var, *[i for i in range(0, 60)])
        self.minute_option.grid(row= 0, column= 4, padx= 5, pady= 5)

        self.next_reset_label = tk.Label(master= self.time_frame, text= self.raw_reset_date_str.format(d= self.reset_day.day, mo= self.reset_day.month, y= self.reset_day.year, h= self.reset_day.hour, m= self.reset_day.minute)) # Das ist Quatsch
        self.next_reset_label.grid(row= 1, column= 0, columnspan= 3, pady= 5, padx= 5, sticky= "w")


        # # Einstellungen für den Timer:
        # self.timer_options_label = tk.Label(master= self, text= "Timer Einstellungen:")
        # self.timer_options_label.pack(padx= 10, pady= (10, 0), anchor= "nw")

        # self.clock_frame = tk.Frame(master= self, borderwidth= 2, relief= "raised")
        # self.clock_frame.pack(padx= 10, pady= 10, fill= "x", expand= True, anchor= "n")

        # self.timer_refresh_label = tk.Label(master= self.clock_frame, text= "Timer aktualisierungsrate in sekunden: ")
        # self.timer_refresh_label.grid(row= 0, column= 0)  

        # self.refresh_entry = tk.Entry(master= self.clock_frame, width= 10)
        # self.refresh_entry.grid(row= 0, column= 1, padx= 5, pady= 5)


        # Darkmode Button
        self.mode_frame = tk.Frame(master= self)
        self.mode_frame.pack(padx= 10, anchor= "nw", fill= "x", expand= True)
        
        self.darkmode_label = tk.Label(master= self.mode_frame, text= "Darkmode")
        self.darkmode_label.grid(row= 0, column= 0, pady= 5, padx= 5)

        self.darkmode_checkbutton = tk.Checkbutton(master= self.mode_frame, offvalue= False, onvalue= True, variable= self.d_mode_var)
        self.darkmode_checkbutton.grid(row=0, column= 1, pady= 5)


        # Update Button --> nicht in .EXE
        self.update_button = tk.Button(master= self, text= "Update", command= lambda: update.update(app_instance= self.master))
        self.update_button.pack(padx= 15, pady= 5, anchor= "nw")


        # Label mit dem Pfad zum Ordner, öffnet bei Linksklick den Explorer
        self.project_path = pathlib.Path(__file__).parent.parent
        self.project_path_label = tk.Label(master=self, text= self.project_path)
        self.project_path_label.bind(sequence= "<Button-1>", func= self.open_explorer)

        self.project_path_label.pack(padx= 15, pady= 5, anchor= "nw")


        # Label zum GitHub Repo, öffnet im Standardbrowser bei Linksklick.
        self.gh_label = tk.Label(master= self, text= "GitHub: https://github.com/JustAName3/Jans-TODO-Liste", foreground= "#4176f2", font= "TkDefaultFont 8 underline")
        self.gh_label.pack(padx= 10, pady= 5)
        self.gh_label.bind(sequence= "<Button-1>", func= self.open_github)


        if config.d_mode:
            self.toggle_d_mode()

    
    def open_explorer(self, *args):
        print(self.project_path)
        ret_code = subprocess.call(args= ["explorer.exe", str(self.project_path)], shell= True)

        logger.info(f"{self.project_path} im Explorer geöffnet")


    def get_timer_refresh_time(self):
        """
        Prüft ob der Wert in den Entries für den Timer refresh ein Int ist. 
        """
        pass


    def update_reset_label(self, *args) -> datetime.datetime:
        """
        Aktualisiert das Label mit dem nächsten Reset Datum.
        """
        weekday: int = config.days.index(self.day_var.get())
        hour = self.hour_var.get()
        minute = self.minute_var.get()

        next_reset_date = functions.next_reset_date(due_day= weekday, time= (hour, minute))

        self.next_reset_label.configure(text= self.raw_reset_date_str.format(d= next_reset_date.day, mo= next_reset_date.month, y= next_reset_date.year, h= next_reset_date.hour, m= next_reset_date.minute))
        self.reset_day = next_reset_date

        return next_reset_date


    def save(self):
        """
        Speichert alle Einstellungen in config.yaml.
        """
        data = {
            "reset_tag": self.day_var.get(),
            "reset_stunde": self.hour_var.get(),
            "reset_minute": self.minute_var.get(),
            "d_mode": self.d_mode_var.get(),
            "konsole": False,
            "timer_refresh": 60000,     # 60.000ms = 1min
            "timer_refresh_24h": 1000   # 1s
        }
        
        with open(config.config_path, "w+") as file:
            yaml_str = yaml.dump(data= data)
            file.write(yaml_str)


    def d_mode_save(self, *args):
        """
        Toggelt den Darkmode und speichert die Einstellungen.
        """
        self.save()
        config.load_config()

        for task in self.master.tasks:
            task.toggle_d_mode()

        self.master.toggle_d_mode()

        self.toggle_d_mode()



    def next_reset_save(self, *args):
        """
        Updatet das next_reset_label und speichert die Einstellungen.
        """
        date = self.update_reset_label()
        logger.info(f"Reset Tag auf {config.days[date.weekday()]} {date.hour}:{date.minute} Uhr gesetzt. Nächster Reset: {date}")

        self.save()

        self.master.due_day = date
        self.master.save_tasks()

        config.load_config()
        self.master.refresh()
        self.master.time()

    
    def open_github(self, event):
        """
        Öffnet das GitHub Repo dieses Projekts im Standardbrowser.
        event ist für .bind auf das gh_label.
        """
        ret_code = subprocess.call(args= ["start", "https://github.com/JustAName3/Jans-TODO-Liste"], shell= True)

        logger.info(f"GitHub Repo im Browser geöffnet, Return Code: {ret_code}")


    def toggle_d_mode(self):
        bg_color = config.bg_color
        tx_color = config.tx_color
        
        # Farbe vom Windows Fenster ändern
        try:
            if platform.system() == "Windows":
                # Kopiert von https://www.youtube.com/watch?v=36PpT4Z22Os
                # KEINE AHNUNG WIE DAS HIER FUNKTIONIERT!
                HWND = ctypes.windll.user32.GetParent(self.winfo_id())
                win_color = 0x00ffffff if not config.d_mode else config.win_color
                # Keine Ahnung was das returned und ob das wirklich der return Code sein soll.
                ret_code = ctypes.windll.dwmapi.DwmSetWindowAttribute(HWND,
                                                                      35,
                                                                      ctypes.byref(ctypes.c_int(win_color)),
                                                                      ctypes.sizeof(ctypes.c_int))
                logger.debug(f"Fenster Farbe geändert (Settings). Return Code(?): {ret_code}")
            
            else:
                logger.debug("Fenster Farbe nicht geändert (Settings). OS != Windows")
        except:
            # Keine Ahung welche Exceptions hier entstehen können, lieber alle abfangen.
            logger.exception("Exception durch Fesnter Farbänderung: ")

        self.configure(background= bg_color)

        self.time_options_label.configure(background= bg_color, foreground= tx_color)
        self.time_frame.configure(background= bg_color)

        self.day_option.configure(background= bg_color, foreground= tx_color, activebackground= bg_color, activeforeground= tx_color, highlightthickness= 0)
        self.day_option["menu"].configure(background= bg_color, foreground= tx_color)

        self.hour_label.configure(background= bg_color, foreground= tx_color)
        self.hour_option.configure(background= bg_color, foreground= tx_color, activebackground= bg_color, activeforeground= tx_color, highlightthickness= 0)
        self.hour_option["menu"].configure(background= bg_color, foreground= tx_color)
        
        self.minute_label.configure(background= bg_color, foreground= tx_color)
        self.minute_option.configure(background= bg_color, foreground= tx_color, activebackground= bg_color, activeforeground= tx_color, highlightthickness= 0)
        self.minute_option["menu"].configure(background= bg_color, foreground= tx_color)
        
        self.next_reset_label.configure(background= bg_color, foreground=tx_color)

        self.mode_frame.configure(background= bg_color)
        self.darkmode_label.configure(background= bg_color, foreground= tx_color)
        self.darkmode_checkbutton.configure(background= bg_color, foreground= bg_color, activebackground= bg_color, activeforeground= tx_color)

        self.project_path_label.configure(background= bg_color, foreground= tx_color)

        self.gh_label.configure(background= bg_color)