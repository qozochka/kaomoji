import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                             QLineEdit, QPushButton, QListWidget,
                             QDialog, QFormLayout, QDialogButtonBox,
                             QMessageBox, QHBoxLayout, QListWidgetItem,
                             QLabel, QSizePolicy)
from PyQt5.QtCore import Qt

KAOMODZI_DATA = ["(^_^)", "(>_<)", "(¬_¬)", "（╯°□°）╯︵ ┻━┻", "(≧∇≦)/", "(o_o)"]


class AddKaomojiDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить Каомодзи")
        self.setGeometry(200, 200, 400, 100)

        self.kaomoji_input = QLineEdit()

        form_layout = QFormLayout()
        form_layout.addRow("Каомодзи:", self.kaomoji_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)  # type: ignore
        self.button_box.rejected.connect(self.reject)  # type: ignore

        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def get_kaomoji(self):
        kaomoji = self.kaomoji_input.text().strip()
        return kaomoji


class KaomojiApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kaomoji Helper")
        self.setGeometry(100, 100, 600, 400)
        self.kaomoji_data = KAOMODZI_DATA

        self.results_list = QListWidget()
        self.populate_kaomoji_list()

        self.add_button = QPushButton("Добавить Каомодзи")
        self.add_button.clicked.connect(self.add_kaomoji)  # type: ignore

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.results_list)
        main_layout.addWidget(self.add_button)

        self.setLayout(main_layout)

    def add_kaomoji(self):
        dialog = AddKaomojiDialog(self)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            kaomoji = dialog.get_kaomoji()
            if kaomoji:
                if kaomoji in self.kaomoji_data:
                    QMessageBox.warning(self, "Ошибка", "Такой каомодзи уже существует!")
                    return
                self.kaomoji_data.append(kaomoji)
                self.populate_kaomoji_list()
                print(f"Added kaomoji: {kaomoji}")
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
        # Окно подтверждения
        reply = QMessageBox.question(self, 'Удаление',
                                     f"Удалить каомодзи '{kaomoji_to_remove}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            if kaomoji_to_remove in self.kaomoji_data:
                self.kaomoji_data.remove(kaomoji_to_remove)
                self.populate_kaomoji_list()
                print(f"Removed kaomoji: {kaomoji_to_remove}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = KaomojiApp()
    ex.show()
    sys.exit(app.exec_())
