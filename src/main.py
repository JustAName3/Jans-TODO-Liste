import functions
import logging
import log
import gui


VERSION = "v.0.2.0" # Muss mit jedem Update aktualisiert werden


def main():
    app = gui.App()

    app.mainloop()


if __name__ == "__main__":

    logger = logging.getLogger("main")
    logger.info("Started app\n")

    try:
        main()
    except:
        logger.exception("Unerwarteter Fehler")

    logger.info("Closed app\n\n")