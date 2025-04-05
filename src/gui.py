from tkinter import PhotoImage
from PIL import Image, ImageTk
import tkinter as tk
import functions
import pathlib
import logging
import config


import log       # LÖSCHEN

logger = logging.getLogger("main.gui") 
data_path = pathlib.Path(__file__).parent.parent / "data.json" # Pfad zur Datei mit den Daten
assets_path = pathlib.Path(__file__).parent.parent / "assets"



class App(tk.Tk):

    def __init__(self, data):

        super().__init__()
        config.load_config()

        self.title("Jans TODO Liste")
        self.iconbitmap(assets_path / "done.ico")
        self.geometry("1050x600")

        self.tasks: list = [] # Hier werden alle Task Instanzen gespeichert.
        self.data: list = data # Alle Daten der Tasks werden hier gespeichert. 
        self.due_day = functions.next_reset_date(due_day= config.due_day, time= config.due_time) # Nächster reset
       
        self.new_button = tk.Button(master= self, text= "Neu", command= self.add_task)
        self.new_button.pack(padx= 10, pady= 10, anchor= "w")


        self.main_frame = tk.Frame(master= self)
        self.main_frame.pack(anchor= "w", fill= "both", expand= True, side= "left")

        self.canvas = tk.Canvas(master= self.main_frame)

        self.inner_frame = tk.Frame(master= self.canvas)
        self.inner_frame.bind("<Configure>", lambda event: self.canvas.configure(scrollregion= self.canvas.bbox("all")))
        self.inner_frame.bind("<MouseWheel>", lambda event: self.scroll(event= event))

        self.canvas_window = self.canvas.create_window((0, 0), window= self.inner_frame)

        self.scrollbar = tk.Scrollbar(master= self.main_frame, orient="vertical", command= self.canvas.yview)
        self.canvas.configure(yscrollcommand= self.scrollbar.set)
        
        self.scrollbar.pack(side= "right", fill= "y")
        self.canvas.pack(fill= "both", expand= True)
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfig(self.canvas_window, width= event.width))

        self.build_menu()
        self.after(1, lambda: self.canvas.yview_moveto(0))

    # adds new tasks 
    def add_task(self):
        t = CreateTask(master= self)
    

    def scroll(self, event):
        self.canvas.yview_scroll(int(-event.delta / 60), "units")
    

    def build_menu(self):
        """
        Erstellt Instanzen von Task und packt diese in self.main_frame.
        """
        ind = 0
        for task in self.data:
            self.tasks.append(Task(master= self.inner_frame,
                                   title= task["title"],
                                   note= task["note"],
                                   done= task["done"],
                                   index= ind,
                                   app= self),
                                   )
            ind += 1
        
        for task in self.tasks:
            task.bind("<MouseWheel>", lambda event: self.scroll(event))
        
        self.inner_frame.columnconfigure(0, weight= 1)
        row = 0
        for task in self.tasks:
            task.grid(row= row, column= 0, pady= 5, padx= 10, sticky= "ew")
            row += 1


    def refresh(self):
        for frame in self.tasks:
            frame.destroy()
        
        self.tasks.clear()

        self.build_menu()


    def delete_task(self, task: int):
        """
        Löscht Tasks aus der Liste und refreshed.
        """
        del self.data[task] 

        functions.write(data= self.data)

        self.refresh()

    
    def time(self):
        pass



class Task(tk.Frame):

    def __init__(self, master, title, note, done, index, app):
        super().__init__(master)

        self.configure(relief= "raised", borderwidth= 2)

        self.title = title
        self.note = note
        self.done = done # Wird True wenn erledigt
        self.app = app # Instanz der haupt App, damit man leichter die methoden ausführen kann.

        self.index = index # Index der Daten in App.data
        with Image.open(assets_path / "done.png")as img:
            img = img.resize((30, 30))
            self.done_img = ImageTk.PhotoImage(img)
        
        with Image.open(assets_path / "notdone.png") as img:
            img = img.resize((30, 30))
            self.not_done_img = ImageTk.PhotoImage(img)


        self.done_button = tk.Button(master= self,
                                     relief= "flat",
                                     command= self.toggle_done)
        self.done_button.bind("<MouseWheel>", lambda event: self.app.scroll(event))
        self.done_button.grid(row= 0, column= 0, padx= 5, pady= 5, rowspan= 2)
        if self.done is False:
            self.done_button.configure(image= self.not_done_img)
        else:
            self.done_button.configure(image= self.done_img)

        self.title_label = tk.Label(master= self,
                                    text= self.title,
                                    font= "TkDefaultFont 14 bold",
                                    wraplength= 1000)
        self.title_label.bind("<MouseWheel>", lambda event: self.app.scroll(event))
        self.title_label.grid(row= 0, column= 1, padx= (0, 10))

        self.note_message = tk.Message(master= self,
                                       text= self.note)
        self.note_message.bind("<MouseWheel>", lambda event: self.app.scroll(event))
        self.note_message.grid(row= 1, column= 1, padx= (0, 10))

        self.bind("<Configure>", self.update_width)


    def toggle_done(self):
        """
        Stellt done auf True und wechselt das Bild.
        """
        self.done = not self.done
        
        if self.done:
                self.done_button.configure(image= self.done_img)
        else:
            self.done_button.configure(image= self.not_done_img)

        self.app.data[self.index]["done"] = self.done
        
        functions.write(data= self.app.data, path= data_path)


    # Sorgt dafür, dass sich der Text an die Größe anpasst
    def update_width(self, event):
        new = event.width - 60

        self.note_message.configure(width= new)
        self.title_label.configure(wraplength= new)


class CreateTask(tk.Toplevel):

    def __init__(self, master):
        
        super().__init__(master)

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


    def clear(self):
        self.title_entry.delete(0, "end")
        self.note_text.delete(1.0, "end")


    def save(self):
        """
        Holt den Text aus den Entries und übergibt die Daten an den master.
        """
        title = self.title_entry.get()
        note = self.note_text.get(1.0, "end-1c")

        if title == "":
            logger.info("No title given, returning")
            return 

        data = {
            "title": title,
            "note": note,
            "done": False
        }

        self.master.data.append(data)

        functions.write(data= self.master.data, path= data_path)

        self.master.refresh()

        self.clear()


dat = functions.read(path= data_path)

app = App(data= dat)

app.mainloop()