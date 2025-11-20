from __future__ import annotations

import logging
from pathlib import Path

LOG_PATH = Path.home() / ".conversor_audio" / "app.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_logger() -> logging.Logger:
    logger = logging.getLogger("conversor_audio")
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
