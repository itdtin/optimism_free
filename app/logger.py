from typing import Any
from queue import Queue


class Logger:
    def __init__(self, log_bufer: Queue) -> None:
        self.row_number = 1
        self.log_bufer = log_bufer

    def log(self, text: Any) -> None:
        self.log_bufer.put(f"{self.row_number} | {text}\n")
        self.row_number += 1


log_bufer = Queue()
logger = Logger(log_bufer)
