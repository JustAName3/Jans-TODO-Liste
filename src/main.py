import functions
import pathlib
import logging
import log
import gui


version_path = pathlib.Path(__file__).parent.parent / "version.txt"
with open(version_path, "r") as file:
    VERSION = file.read() # Muss mit jedem Update aktualisiert werden


def main():
    app = gui.App()

    app.mainloop()


if __name__ == "__main__":

    logger = logging.getLogger("main")
    logger.info(f"App gestartet (Version: {VERSION})\n")

    try:
        main()
    except:
        logger.exception("Unerwarteter Fehler")

    logger.info("App geschlossen\n\n")