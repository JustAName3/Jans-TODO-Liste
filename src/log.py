import logging.config
import pathlib
import os

file_path = pathlib.Path(__file__).parent.parent / "logs"
stdout_level = "DEBUG"
backup_count = 1
log_file_size = 100000 # 100kB

logger = {
    "version": 1,
    "disable_existing_logger": False,

    "formatters": {
        "standard": {
            "format": "<%(asctime)s> %(levelname)s|%(name)s| Function: %(funcName)s -> %(message)s"
        }
    },

    "handlers": {
        "stdout": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "standard"
        },

        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": file_path / "log.log",
            "formatter": "standard",
            "level": "INFO",
            "maxBytes": log_file_size,
            "backupCount": backup_count
        },

        "debug_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "standard",
            "filename": file_path / "debug.log",
            "level": "DEBUG",
            "maxBytes": log_file_size,
            "backupCount": backup_count
        }
    },

    "loggers": {
        "main": {
            "level": "DEBUG",
            "handlers": ["stdout", "file", "debug_file"],
            "propagate": False
        },

        "main.gui": {
            "level": "DEBUG",
            "propagate": True
        },

        "main.functions": {
            "level": "DEBUG",
            "propagate": True
        },

        "main.update": {
            "level": "DEBUG",
            "propagate": True
        }
    }
}



if file_path.exists() is False:
    os.mkdir(file_path)
    print(file_path)


logging.config.dictConfig(config= logger)