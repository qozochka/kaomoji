import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                             QLineEdit, QPushButton, QListWidget,
                             QDialog, QFormLayout, QDialogButtonBox,
                             QMessageBox, QHBoxLayout, QListWidgetItem,
                             QLabel, QSizePolicy, QCheckBox, QLineEdit, QCompleter)
from PyQt5.QtCore import Qt
from KaomojiDatabase import KaomojiDatabase

class AddKaomojiDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить Каомодзи")
        self.setGeometry(200, 200, 400, 150)

        self.kaomoji_input = QLineEdit()
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Введите теги через запятую")

        form_layout = QFormLayout()
        form_layout.addRow("Каомодзи:", self.kaomoji_input)
        form_layout.addRow("Теги (через запятую):", self.tags_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def get_kaomoji(self):
        kaomoji = self.kaomoji_input.text().strip()
        tags_str = self.tags_input.text().strip()
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
        return kaomoji, tags

class KaomojiApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kaomoji Helper")
        self.setGeometry(100, 100, 600, 450)
        self.db = KaomojiDatabase()
        self.sort_by_date = True
        self.search_tags = []
        self.kaomoji_data = self.load_kaomoji_data()

        self.results_list = QListWidget()
        self.populate_kaomoji_list()

        self.add_button = QPushButton("Добавить Каомодзи")
        self.add_button.clicked.connect(self.add_kaomoji)

        self.sort_checkbox = QCheckBox("Сортировать по дате")
        self.sort_checkbox.setChecked(self.sort_by_date)
        self.sort_checkbox.stateChanged.connect(self.toggle_sort)

        self.search_tags_input = QLineEdit()
        self.search_tags_input.setPlaceholderText("Поиск по тегам (через запятую)")
        self.search_tags_input.returnPressed.connect(self.search_kaomoji_by_tags)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.results_list)
        main_layout.addWidget(self.add_button)
        main_layout.addWidget(self.sort_checkbox)
        main_layout.addWidget(self.search_tags_input)
        self.setLayout(main_layout)

    def load_kaomoji_data(self):
        return self.db.get_all_kaomoji(sort_by_date=self.sort_by_date, search_tags=self.search_tags)

    def toggle_sort(self, state):
        self.sort_by_date = state == Qt.Checked
        self.kaomoji_data = self.load_kaomoji_data()
        self.populate_kaomoji_list()

    def add_kaomoji(self):
        dialog = AddKaomojiDialog(self)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            kaomoji, tags = dialog.get_kaomoji()
            if kaomoji:
                if kaomoji in self.kaomoji_data:
                    QMessageBox.warning(self, "Ошибка", "Такой каомодзи уже существует!")
                    return

                if self.db.add_kaomoji(kaomoji, tags):
                    self.kaomoji_data = self.load_kaomoji_data()
                    self.populate_kaomoji_list()
                    print(f"Added kaomoji: {kaomoji} with tags: {tags}")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось добавить каомодзи.")
            else:
                QMessageBox.warning(self, "Ошибка", "Каомодзи не может быть пустым!")

    def populate_kaomoji_list(self):
        self.results_list.clear()
        for kaomoji in self.kaomoji_data:
            item = QListWidgetItem()
            widget = QWidget()
            layout = QHBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            kaomoji_label = QLabel(kaomoji)
            layout.addWidget(kaomoji_label)

            # tags = self.db.get_tags_for_kaomoji(kaomoji)
            # if tags:
            #     tags_label = QLabel(f"[{', '.join(tags)}]")
            #     layout.addWidget(tags_label)

            del_button = QPushButton()
            del_button.setStyleSheet("""
                QPushButton {
                    color: black;
                    font-weight: bold;
                    border: none;
                    min-width: 20px;
                    max-width: 20px;
                    min-height: 20px;
                    max-height: 20px;
                    margin-right: 0px;
                }
                QPushButton:hover {
                    background-color: lightgray;
                    color: red;
                    font-size: 16px;
                }
            """)
            del_button.setText("✖")
            del_button.clicked.connect(lambda checked, k=kaomoji: self.remove_kaomoji(k))  # type: ignore
            layout.addWidget(del_button)

            kaomoji_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

            layout.setAlignment(Qt.AlignRight)

            widget.setLayout(layout)

            item.setSizeHint(widget.sizeHint())

            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, widget)

    def remove_kaomoji(self, kaomoji_to_remove):
        reply = QMessageBox.question(self, 'Удаление',
                                     f"Удалить каомодзи '{kaomoji_to_remove}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            if self.db.remove_kaomoji(kaomoji_to_remove):
                self.kaomoji_data = self.load_kaomoji_data()
                self.populate_kaomoji_list()
                print(f"Removed kaomoji: {kaomoji_to_remove}")

    def search_kaomoji_by_tags(self):
        search_text = self.search_tags_input.text().strip()
        self.search_tags = [tag.strip() for tag in search_text.split(",") if tag.strip()]
        self.kaomoji_data = self.load_kaomoji_data()
        self.populate_kaomoji_list()

    def closeEvent(self, event):
        self.db.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = KaomojiApp()
    ex.show()
    sys.exit(app.exec_())
