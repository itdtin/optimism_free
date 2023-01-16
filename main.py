import sys
import time
from pathlib import Path
from threading import Thread
from json import dump, load
from typing import Any

from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow
from app.design import Ui_MainWindow, STRINGS, LANGUAGE
from app.logger import logger
from app.quests_runner import QuestRunner
from app.states import state


class QuestRunnerConfig:
    api_key: str
    quests_to_run: str
    file_name: str
    min_wait_wlt: int
    max_wait_wlt: int
    min_wait_quest: int
    max_wait_quest: int
    type_of_running: str
    window: Any

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if key in ("min_wait_wlt", "max_wait_wlt", "min_wait_quest", "max_wait_quest"):
                if (isinstance(value, str) and value.isdigit()) or isinstance(value, int):
                    value = int(value)
                else:
                    raise ValueError(
                        f"Invalid value for int field {key}. Get: {type(value)}")
            setattr(self, key, value)

    def dump(self):
        to_dump = self.__dict__
        if to_dump.get("window"):
            to_dump.pop("window")
        with open("config.json", "w", encoding="utf-8") as file:
            dump(to_dump, file, indent=4)

    def load(self):
        with open("config.json", "r", encoding="utf-8") as file:
            data = load(file)
            if data.get("window"):
                data.pop("window")
            return self.__init__(**data)

    def __getitem__(self, key):
        return self.__dict__[key]

    def keys(self):
        return self.__dict__.keys()


class Window(QMainWindow):
    config_file = "./config.json"
    work_thread: Thread
    log_thread: Thread
    questRunner: QuestRunner

    def __init__(self):
        super(Window, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.finish_quests.close()
        self.file_name = ""
        self.quests_runner_config = QuestRunnerConfig()
        self.check_last_start()

        self.start_log()

        self.ui.start_btn.clicked.connect(self.get_start)
        self.ui.import_wallets_btn.clicked.connect(self.open_file)
        self.ui.change_lang.clicked.connect(self.change_lang)
        self.ui.finish_quests.clicked.connect(self.finish_quests_running)

    def start_log(self):
        self.log_thread = Thread(
            target=self.log, name="log_thread", daemon=True)
        self.log_thread.start()

    def change_lang(self):
        global LANGUAGE
        if LANGUAGE == "EN":
            LANGUAGE = "RU"
        else:
            LANGUAGE = "EN"
        state.set_language(LANGUAGE)
        self.ui.change_lang.setText(STRINGS[LANGUAGE]["change_lang"])

        self.ui.infobox_label.setText(STRINGS[LANGUAGE]["infobox_label"])
        self.ui.infobox_label.setOpenExternalLinks(True)

        # self.ui.label_api.setText(STRINGS[LANGUAGE]["label_api"])
        # self.ui.label_api.setOpenExternalLinks(True)

        self.ui.import_wallets_btn.setText(STRINGS[LANGUAGE]["import_wallets_btn"])
        self.ui.wait_btw_wlt.setText(STRINGS[LANGUAGE]["wait_btw_wlt"])
        self.ui.min_btw_wlt.setText(STRINGS[LANGUAGE]["wait_from"])
        self.ui.max_btw_wlt.setText(STRINGS[LANGUAGE]["wait_to"])

        self.ui.type_of_running_title.setText(STRINGS[LANGUAGE]["type_of_running_title"])
        self.ui.type_of_running.setItemText(0, STRINGS[LANGUAGE]["type_of_running"][0])
        self.ui.type_of_running.setItemText(1, STRINGS[LANGUAGE]["type_of_running"][1])

        self.ui.quests_choice_label.setText(STRINGS[LANGUAGE]["quests_choice_label"])

        self.ui.wait_btw_quests.setText(STRINGS[LANGUAGE]["wait_btw_quests"])
        self.ui.min_btw_quests.setText(STRINGS[LANGUAGE]["wait_from"])
        self.ui.max_btw_quests.setText(STRINGS[LANGUAGE]["wait_to"])

        self.ui.start_btn.setText(STRINGS[LANGUAGE]["start_btn"])
        self.ui.finish_quests.setText(STRINGS[LANGUAGE]["finish_quests"])
        self.ui.logs_label.setText(STRINGS[LANGUAGE]["logs_label"])

    def open_file(self) -> None:
        file_name = QFileDialog.getOpenFileName(
            self, ("Open .txt with private keys"), "./", ("Text Files (*.txt)")
        )
        self.file_name = file_name[0] if file_name[0] else ""

    def finish_quests_running(self):
        state.set_state(False, LIVE=True, index=0)
        self.work_thread.join()
        self.ui.finish_quests.close()
        logger.log(STRINGS[LANGUAGE]["start_new_quests_running"])
        state.set_state(True, LIVE=True, index=0)
        state.set_state(False, PAUSE=True)
        self.ui.start_btn.setText(STRINGS[LANGUAGE]["start_btn"])

    def get_start(self) -> None:
        text = self.ui.start_btn.text()
        if text == STRINGS[LANGUAGE]["start_btn"]:
            self.ui.change_lang.close()
            self.ui.finish_quests.show()
            self.ui.start_btn.setText(STRINGS[LANGUAGE]["stop"])

            self.update_config()
            self.questRunner = QuestRunner(
                api_key=self.quests_runner_config.api_key,
                quests_to_run=self.quests_runner_config.quests_to_run,
                file_name=self.quests_runner_config.file_name,
                min_wait_wlt=self.quests_runner_config.min_wait_wlt,
                max_wait_wlt=self.quests_runner_config.max_wait_wlt,
                min_wait_quest=self.quests_runner_config.min_wait_quest,
                max_wait_quest=self.quests_runner_config.max_wait_quest,
                type_of_running=self.quests_runner_config.type_of_running,
                window=self.quests_runner_config.window
            )
            self.start_work()
        elif text == STRINGS[LANGUAGE]["continue"]:
            state.set_state(False, PAUSE=True)
            self.ui.start_btn.setText(STRINGS[LANGUAGE]["stop"])
            self.questRunner.quests_to_run = [item.text() for item in self.ui.quests_to_dep_box.list_of_checkboxes if item.isChecked()]
            self.start_work()
        elif text == STRINGS[LANGUAGE]["stop"]:
            logger.log(STRINGS[LANGUAGE]["log_stop"])
            state.set_state(True, PAUSE=True)
            self.ui.start_btn.setText(STRINGS[LANGUAGE]["continue"])
            self.work_thread.join()
        else:
            state.set_state(False, LIVE=True, index=0)
            state.set_state(False, LIVE=True, index=1)
            self.log_thread.join()
            self.work_thread.join()
            sys.exit()

    def stop_work(self) -> None:
        self.ui.start_btn.setText(STRINGS[LANGUAGE]["continue"])

    def start_work(self) -> None:
        self.work_thread = Thread(
            target=self.questRunner.do_work, name="work_thread", daemon=True)
        self.work_thread.start()

    def log(self):
        while state.get_state(LIVE=True, index=1):
            while logger.log_bufer.qsize():
                self.ui.textBrowser.insertPlainText(logger.log_bufer.get())
                scroll = self.ui.textBrowser.verticalScrollBar()
                scroll.setValue(scroll.maximum())
                time.sleep(0.5)
            time.sleep(1)

    def check_last_start(self) -> None:
        """Подгрузка параметров прошлого запуска."""

        if Path(self.config_file) in set(Path().iterdir()):
            self.quests_runner_config.load()
            self.set_config()

    def update_config(self) -> None:
        """Обновление и сохранение конфига."""

        self.quests_runner_config.api_key = self.ui.api_key_row.text()
        self.quests_runner_config.file_name = self.file_name
        self.quests_runner_config.min_wait_wlt = int(self.ui.min_wait_wlt.text())
        self.quests_runner_config.max_wait_wlt = int(self.ui.max_wait_wlt.text())
        self.quests_runner_config.min_wait_quest = int(self.ui.min_wait_quest.text())
        self.quests_runner_config.max_wait_quest = int(self.ui.max_wait_quest.text())
        self.quests_runner_config.type_of_running = self.ui.type_of_running.currentText()

        self.quests_runner_config.quests_to_run = [item.text() for item in self.ui.quests_to_dep_box.list_of_checkboxes if item.isChecked()]
        self.quests_runner_config.dump()
        self.quests_runner_config.window = self

    def set_config(self) -> None:
        """Установка значений из конфига."""

        if self.quests_runner_config["type_of_running"].isascii() == False:
            self.change_lang()
        # self.ui.api_key_row.setText(self.quests_runner_config["api_key"])
        self.file_name = self.quests_runner_config["file_name"]
        self.ui.min_wait_wlt.setValue(self.quests_runner_config["min_wait_wlt"])
        self.ui.max_wait_wlt.setValue(self.quests_runner_config["max_wait_wlt"])
        self.ui.min_wait_quest.setValue(self.quests_runner_config["min_wait_quest"])
        self.ui.max_wait_quest.setValue(self.quests_runner_config["max_wait_quest"])
        self.ui.type_of_running.setCurrentText(self.quests_runner_config["type_of_running"])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
