import log
# import gui
import functions
import logging


VERSION = "v.0.0.0" # Muss mit jedem Update aktualisiert werden


def main():
    ...


if __name__ == "__main__":

    logger = logging.getLogger("main")
    logger.info("Started app\n")

    main()

    logger.info("Closed app\n\n")