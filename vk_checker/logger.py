from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(level: str = "INFO") -> None:
    Path("logs").mkdir(exist_ok=True)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    app_file = RotatingFileHandler("logs/app.log", maxBytes=10_000_000, backupCount=5, encoding="utf-8")
    app_file.setFormatter(formatter)
    app_file.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.addHandler(app_file)

    err_file = RotatingFileHandler("logs/errors.log", maxBytes=10_000_000, backupCount=5, encoding="utf-8")
    err_file.setFormatter(formatter)
    err_file.setLevel(logging.ERROR)
    root.addHandler(err_file)
