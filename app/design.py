from pathlib import Path
from typing import Literal

from PySide6.QtCore import QMetaObject, QSize, Qt, QEvent
from PySide6.QtGui import QIcon, QStandardItem
from PySide6.QtWidgets import (QComboBox, QLabel, QLineEdit, QPushButton,
                               QSizePolicy, QTextBrowser, QVBoxLayout, QWidget, QHBoxLayout, QSpinBox, QCheckBox)


LANGUAGE: Literal["RU", "EN"] = "EN"

STRINGS = {
    "RU": {
        "change_lang": "Change to English",
        "infobox_label": """Программа для автоматичесгого выполнения Optimism Quests🚀 <a href="https://t.me/softbot_eth"><В канал>>👇<a>""",
        "import_wallets_btn": "Импорт кошельков (Txt файл с приватными ключам кошельков)",
        "wait_btw_wlt": "Границы рандомной задержки между кошельками",
        "wait_from": "От",
        "wait_to": "до",
        "wait_btw_quests": "Границы рандомной задержки между квестами",
        "quests_choice_label": "Выберите квесты для запуска",
        "type_of_running_title": "Выберите режим работы программы",
        "type_of_running": {
            0: "Запуск квестов",
            1: "Вывод из протоколов"
        },
        "start_btn": "Старт",
        "logs_label": "Логи",
        "stop": "Стоп",
        "continue": "Продолжить",
        "finish_quests": "Завершить квесты",
        "start_new_quests_running": "Вы можете запустить квесты снова",
        "log_load_wlt": "Кошельки загружены",
        "log_return_points": "Возврат поинтов за неудачные квесты: %s",
        "not_enough_points_log": "Недостаточный баланс для запуска квеста. Пополните баланс в боте  и сможете продолжить с того же места",
        "log_done": "Завершено",
        "log_pause": "Пауза {} сек",
        "log_check_back": "Проверьте бэкенд для параметров %s %s",
        "log_stop": "Called STOP. Will affect after current running part of quests",
    },
    "EN": {
        "change_lang": "Переключить на Русский",
        "infobox_label": """It's a programm to pass Optimism Quests automatically🚀 <a href="https://t.me/softbot_eth">More about automation👇<a>""",
        "import_wallets_btn": "Import wallets (Txt file with private keys of wallets)",
        "wait_btw_wlt": "Random delay range between wallets in seconds",
        "wait_btw_quests": "Random delay range between quests in seconds",
        "wait_from": "From",
        "wait_to": "to",
        "type_of_running_title": "Choose the type of quests running",
        "type_of_running": {
            0: "Run quests",
            1: "Withdraw from protocols"
        },
        "quests_choice_label": "Choose quests to run",
        "start_btn": "Start",
        "logs_label": "Logs",
        "stop": "Stop",
        "continue": "Continue",
        "finish_quests": "End quests running",
        "start_new_quests_running": "You can start quests running again",
        "log_load_wlt": "Wallets loaded",
        "log_return_points": "Points returned for failed quests: %s",
        "not_enough_points_log": "Insufficient balance for quest running. Refill balance in bot and you can continue from the same place",
        "log_done": "Done",
        "log_pause": "Pause {} seconds",
        "log_check_back": "Please check your backend service %s %s",
        "log_stop": "Called STOP. Will affect after current running part of quests",
    }
}
quests_choices = [
    "7 Quests: Uniswap, Velodrome, Synapse, Rubicon, Pika, Perp, Granary(required 0.046 ETH(~55$ + gas) in OPTIMISM)",
]


class CheckBoxGroup:
    def __init__(self, centralwidget, layout, names):
        self.list_of_checkboxes = [QCheckBox(name, centralwidget) for name in names]
        for choice_checkbox in self.list_of_checkboxes:
            choice_checkbox.setChecked(True)
            layout.addWidget(choice_checkbox)

    def show_close(self, show=None, close=None):
        for checkbox in self.list_of_checkboxes:
            if show:
                checkbox.show()
            elif close:
                checkbox.close()

    def get_text(self, index):
        item = self.list_of_checkboxes[index]
        return item.isChecked()


class Ui_MainWindow(object):
    def setup_common_window(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 750)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        icon = QIcon()
        iconThemeName = "accessories-character-map"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(Path("favicon.ico").as_posix(),
                         QSize(), QIcon.Normal, QIcon.On)

        MainWindow.setWindowIcon(icon)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        sizePolicy.setHeightForWidth(
            self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setMinimumSize(QSize(800, 750))
        self.centralwidget.setMaximumSize(QSize(1960, 1080))
        self.centralwidget.setBaseSize(QSize(700, 900))
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")

    def setup_infobox(self):
        self.infobox_label = QLabel(self.centralwidget)
        self.infobox_label.setObjectName("infobox_label")
        self.verticalLayout.addWidget(self.infobox_label)

    def setup_change_lang(self):
        self.change_lang = QPushButton(self.centralwidget)
        self.change_lang.setObjectName("change_lang")
        self.verticalLayout.addWidget(self.change_lang)
    #
    # def setup_api_key(self):
    #     self.label_api = QLabel(self.centralwidget)
    #     self.label_api.setObjectName("label_api")
    #     self.verticalLayout.addWidget(self.label_api)
    #
    #     self.api_key_row = QLineEdit(self.centralwidget)
    #     self.api_key_row.setObjectName("api_key_row")
    #     self.api_key_row.setFrame(False)
    #     self.verticalLayout.addWidget(self.api_key_row)

    def setup_import_wallets(self):
        self.import_wallets_btn = QPushButton(self.centralwidget)
        self.import_wallets_btn.setObjectName("import_wallets_btn")

        self.verticalLayout.addWidget(self.import_wallets_btn)

    def setup_waiting_btw_wlt(self):
        self.wait_btw_wlt = QLabel(self.centralwidget)
        self.wait_btw_wlt.setObjectName("wait_btw_wlt")

        self.verticalLayout.addWidget(self.wait_btw_wlt)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.min_btw_wlt = QLabel(self.centralwidget)
        self.min_btw_wlt.setObjectName("min_btw_wlt")

        self.horizontalLayout.addWidget(self.min_btw_wlt)

        self.min_wait_wlt = QSpinBox(self.centralwidget)

        self.min_wait_wlt.setObjectName("min_wait_wlt")

        self.horizontalLayout.addWidget(self.min_wait_wlt)

        self.max_btw_wlt = QLabel(self.centralwidget)

        self.max_btw_wlt.setObjectName("max_btw_wlt")

        self.horizontalLayout.addWidget(self.max_btw_wlt)

        self.max_wait_wlt = QSpinBox(self.centralwidget)
        self.max_wait_wlt.setMaximum(999)
        self.max_wait_wlt.setObjectName("max_wait_wlt")

        self.horizontalLayout.addWidget(self.max_wait_wlt)

        self.verticalLayout.addLayout(self.horizontalLayout)

    def setup_waiting_btw_quests(self):
        self.wait_btw_quests = QLabel(self.centralwidget)
        self.wait_btw_quests.setObjectName("wait_btw_quests")

        self.verticalLayout.addWidget(self.wait_btw_quests)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.min_btw_quests = QLabel(self.centralwidget)
        self.min_btw_quests.setObjectName("min_btw_quests")

        self.horizontalLayout.addWidget(self.min_btw_quests)

        self.min_wait_quest = QSpinBox(self.centralwidget)
        self.min_wait_quest.setObjectName("min_wait_quest")

        self.horizontalLayout.addWidget(self.min_wait_quest)

        self.max_btw_quests = QLabel(self.centralwidget)
        self.max_btw_quests.setObjectName("max_btw_quests")

        self.horizontalLayout.addWidget(self.max_btw_quests)

        self.max_wait_quest = QSpinBox(self.centralwidget)
        self.max_wait_quest.setMaximum(999)
        self.max_wait_quest.setObjectName("max_wait_quest")

        self.horizontalLayout.addWidget(self.max_wait_quest)

        self.verticalLayout.addLayout(self.horizontalLayout)

    def setup_type_of_running(self):
        self.type_of_running_title = QLabel(self.centralwidget)
        self.type_of_running_title.setObjectName("type_of_running_title")

        self.verticalLayout.addWidget(self.type_of_running_title)

        self.type_of_running = QComboBox(self.centralwidget)
        self.type_of_running.addItem("")
        self.type_of_running.addItem("")
        self.type_of_running.setObjectName("type_of_running")
        self.verticalLayout.addWidget(self.type_of_running)

    def setup_finish(self):
        self.finish_quests = QPushButton(self.centralwidget)
        self.finish_quests.setObjectName("finish_quests")
        self.verticalLayout.addWidget(self.finish_quests)

    def setup_start(self):
        self.start_btn = QPushButton(self.centralwidget)
        self.start_btn.setObjectName("start_btn")
        self.verticalLayout.addWidget(self.start_btn)

    def setup_quests_choice(self):
        self.quests_choice_label = QLabel(self.centralwidget)
        self.quests_choice_label.setObjectName("quests_choice_label")
        self.quests_choice_label.setAlignment(Qt.AlignCenter)
        self.verticalLayout.addWidget(self.quests_choice_label)
        self.quests_to_dep_box = CheckBoxGroup(self.centralwidget, self.verticalLayout, quests_choices)

    def setup_logs(self):
        self.logs_label = QLabel(self.centralwidget)
        self.logs_label.setObjectName("logs_label")
        self.logs_label.setAlignment(Qt.AlignCenter)
        self.verticalLayout.addWidget(self.logs_label)

        self.textBrowser = QTextBrowser(self.centralwidget)
        self.textBrowser.setObjectName("textBrowser")
        self.textBrowser.setEnabled(True)
        self.verticalLayout.addWidget(self.textBrowser)

    def setupUi(self, MainWindow):
        self.setup_common_window(MainWindow)
        self.setup_infobox()
        self.setup_change_lang()
        # self.setup_api_key()
        self.setup_import_wallets()
        self.setup_type_of_running()
        self.setup_quests_choice()
        self.setup_waiting_btw_wlt()
        self.setup_waiting_btw_quests()
        self.setup_start()
        self.setup_finish()
        self.setup_logs()

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle("Optimism quests")
        self.change_lang.setText(STRINGS[LANGUAGE]["change_lang"])
        self.infobox_label.setText(STRINGS[LANGUAGE]["infobox_label"])
        self.infobox_label.setOpenExternalLinks(True)
        # self.label_api.setText(STRINGS[LANGUAGE]["label_api"])
        # self.label_api.setOpenExternalLinks(True)
        self.import_wallets_btn.setText(STRINGS[LANGUAGE]["import_wallets_btn"])
        self.wait_btw_wlt.setText(STRINGS[LANGUAGE]["wait_btw_wlt"])
        self.min_btw_wlt.setText(STRINGS[LANGUAGE]["wait_from"])
        self.max_btw_wlt.setText(STRINGS[LANGUAGE]["wait_to"])
        self.type_of_running_title.setText(STRINGS[LANGUAGE]["type_of_running_title"])
        self.type_of_running.setItemText(
            0, STRINGS[LANGUAGE]["type_of_running"][0])
        self.type_of_running.setItemText(
            1, STRINGS[LANGUAGE]["type_of_running"][1])

        self.quests_choice_label.setText(STRINGS[LANGUAGE]["quests_choice_label"])

        self.wait_btw_quests.setText(STRINGS[LANGUAGE]["wait_btw_quests"])
        self.min_btw_quests.setText(STRINGS[LANGUAGE]["wait_from"])
        self.max_btw_quests.setText(STRINGS[LANGUAGE]["wait_to"])

        self.start_btn.setText(STRINGS[LANGUAGE]["start_btn"])
        self.finish_quests.setText(STRINGS[LANGUAGE]["finish_quests"])
        self.logs_label.setText(STRINGS[LANGUAGE]["logs_label"])
