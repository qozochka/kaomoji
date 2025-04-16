import sqlite3
import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                             QLineEdit, QPushButton, QListWidget,
                             QDialog, QFormLayout, QDialogButtonBox,
                             QMessageBox, QHBoxLayout, QListWidgetItem,
                             QLabel, QSizePolicy, QCheckBox, QLineEdit, QCompleter,
                             QTextEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QClipboard, QIcon
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

class EditTagsDialog(QDialog):
    def __init__(self, parent, kaomoji, existing_tags):
        super().__init__(parent)
        self.setWindowTitle(f"Редактировать теги для: {kaomoji}")
        self.setGeometry(200, 200, 400, 150)
        self.kaomoji = kaomoji

        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Введите теги через запятую")
        self.tags_input.setText(", ".join(existing_tags))  # Populate with existing tags

        form_layout = QFormLayout()
        form_layout.addRow("Теги (через запятую):", self.tags_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def get_new_tags(self):
        tags_str = self.tags_input.text().strip()
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
        return tags

class KaomojiApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kaomoji Helper")
        self.setGeometry(100, 100, 600, 550)  # Increased window height
        self.db = KaomojiDatabase()
        self.sort_by_date = True
        self.search_tags = []
        self.kaomoji_data = self.load_kaomoji_data()
        self.copied_kaomoji = []  # List to store copied kaomoji

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

        # Copy Buffer Section
        self.copied_kaomoji_text = QTextEdit()
        self.copied_kaomoji_text.setReadOnly(True)  # Make it read-only
        self.copy_button = QPushButton("Копировать в буфер")
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        self.clear_button = QPushButton("Очистить")
        self.clear_button.clicked.connect(self.clear_copied_kaomoji)

        copy_buffer_layout = QHBoxLayout()
        copy_buffer_layout.addWidget(self.copy_button)
        copy_buffer_layout.addWidget(self.clear_button)

        copy_buffer_section_layout = QVBoxLayout()
        copy_buffer_section_layout.addWidget(QLabel("Скопированные Каомодзи:"))
        copy_buffer_section_layout.addWidget(self.copied_kaomoji_text)
        copy_buffer_section_layout.addLayout(copy_buffer_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.results_list)
        main_layout.addWidget(self.add_button)
        main_layout.addWidget(self.sort_checkbox)
        main_layout.addWidget(self.search_tags_input)
        main_layout.addLayout(copy_buffer_section_layout)  # Add the copy buffer section
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

            tags = self.db.get_tags_for_kaomoji(kaomoji)
            if tags:
                tags_label = QLabel(f"[{', '.join(tags)}]")
                layout.addWidget(tags_label)

            # Copy Button
            copy_button = QPushButton("📋")  # Clipboard emoji
            copy_button.setStyleSheet("""
                QPushButton {
                    color: black;
                    font-weight: bold;
                    border: none;
                    min-width: 20px;
                    max-width: 20px;
                    min-height: 20px;
                    max-height: 20px;
                    margin-left: 5px;
                }
                QPushButton:hover {
                    background-color: lightgray;
                    color: blue;
                    font-size: 16px;
                }
            """)
            copy_button.clicked.connect(lambda checked, k=kaomoji: self.copy_kaomoji(k))
            layout.addWidget(copy_button)

            edit_tags_button = QPushButton("✏️") # Use a pencil emoji
            edit_tags_button.setStyleSheet("""
                QPushButton {
                    color: black;
                    font-weight: bold;
                    border: none;
                    min-width: 20px;
                    max-width: 20px;
                    min-height: 20px;
                    max-height: 20px;
                    margin-left: 5px;
                }
                QPushButton:hover {
                    background-color: lightgray;
                    color: green;
                    font-size: 16px;
                }
            """)
            edit_tags_button.clicked.connect(lambda checked, k=kaomoji: self.edit_tags(k))
            layout.addWidget(edit_tags_button)

            del_button = QPushButton("✖")
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
                    margin-left: 5px;
                }
                QPushButton:hover {
                    background-color: lightgray;
                    color: red;
                    font-size: 16px;
                }
            """)
            del_button.clicked.connect(lambda checked, k=kaomoji: self.remove_kaomoji(k))
            layout.addWidget(del_button)

            kaomoji_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

            layout.setAlignment(Qt.AlignRight)

            widget.setLayout(layout)

            item.setSizeHint(widget.sizeHint())

            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, widget)

    def copy_kaomoji(self, kaomoji):
        self.copied_kaomoji.append(kaomoji)
        self.update_copied_kaomoji_text()
        print(f"Copied kaomoji: {kaomoji}")


    def update_copied_kaomoji_text(self):
        self.copied_kaomoji_text.setPlainText(" ".join(self.copied_kaomoji))  # Space between entries

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(" ".join(self.copied_kaomoji))  # Space between entries
        print("Copied to clipboard")

    def clear_copied_kaomoji(self):
        self.copied_kaomoji = []
        self.update_copied_kaomoji_text()
        print("Cleared copied kaomoji")

    def edit_tags(self, kaomoji):
        existing_tags = self.db.get_tags_for_kaomoji(kaomoji)
        dialog = EditTagsDialog(self, kaomoji, existing_tags)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            new_tags = dialog.get_new_tags()
            if self.db.edit_tags(kaomoji, new_tags):
                self.kaomoji_data = self.load_kaomoji_data()
                self.populate_kaomoji_list()

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
