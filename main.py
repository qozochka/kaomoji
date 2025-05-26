import os
import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                             QLineEdit, QPushButton, QListWidget,
                             QDialog, QFormLayout, QDialogButtonBox,
                             QMessageBox, QHBoxLayout, QListWidgetItem,
                             QLabel, QSizePolicy, QCheckBox, QLineEdit, QCompleter,
                             QTextEdit, QSplitter, QInputDialog, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QClipboard, QIcon
from KaomojiDatabase import KaomojiDatabase
import sqlite3

class AddKaomojiDialog(QDialog):
    def __init__(self, parent=None, playlists=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить Каомодзи")
        self.setGeometry(200, 200, 400, 200)

        self.kaomoji_input = QLineEdit()
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Введите теги через запятую")

        self.playlist_combo = QComboBox()
        self.playlist_combo.addItems(playlists)

        form_layout = QFormLayout()
        form_layout.addRow("Каомодзи:", self.kaomoji_input)
        form_layout.addRow("Теги (через запятую):", self.tags_input)
        form_layout.addRow("Подборка:", self.playlist_combo)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def get_kaomoji_data(self):
        kaomoji = self.kaomoji_input.text().strip()
        tags_str = self.tags_input.text().strip()
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
        playlist_name = self.playlist_combo.currentText()
        return kaomoji, tags, playlist_name

class EditTagsDialog(QDialog):
    def __init__(self, parent, kaomoji, existing_tags):
        super().__init__(parent)
        self.setWindowTitle(f"Редактировать теги для: {kaomoji}")
        self.setGeometry(200, 200, 400, 150)
        self.kaomoji = kaomoji

        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Введите теги через запятую")
        self.tags_input.setText(", ".join(existing_tags))

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

class PlaylistManagementWidget(QWidget):
    def __init__(self, parent=None, main_app=None):
        super().__init__(parent)
        self.playlists = ["моя подборка 1", "моя подборка 2"]
        self.playlist_list = QListWidget()
        self.playlist_list.addItem("Все")
        self.playlist_list.addItems(self.playlists)
        self.create_button = QPushButton("Создать подборку")
        self.delete_button = QPushButton("Удалить подборку")
        self.main_app = main_app

        self.create_button.clicked.connect(self.create_playlist)
        self.delete_button.clicked.connect(self.delete_playlist)
        self.playlist_list.itemClicked.connect(self.playlist_selected)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Подборки:"))
        layout.addWidget(self.playlist_list)
        layout.addWidget(self.create_button)
        layout.addWidget(self.delete_button)
        self.setLayout(layout)

    def create_playlist(self):
        playlist_name, ok = QInputDialog.getText(self, "Создать подборку", "Имя подборки:")
        if ok and playlist_name:
            if playlist_name not in self.playlists and playlist_name != "Все":
                self.playlists.append(playlist_name)
                self.playlist_list.addItem(playlist_name)
            else:
                QMessageBox.warning(self, "Ошибка", "Подборка с таким именем уже существует.")

    def delete_playlist(self):
        selected_item = self.playlist_list.currentItem()
        if selected_item and selected_item.text() != "Все":
            playlist_name = selected_item.text()
            reply = QMessageBox.question(self, 'Удаление',
                                        f"Удалить подборку '{playlist_name}'?",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.playlists.remove(playlist_name)
                self.playlist_list.takeItem(self.playlist_list.row(selected_item))
                if self.main_app:
                    self.main_app.load_kaomoji_for_playlist(None)
        elif selected_item and selected_item.text() == "Все":
            QMessageBox.warning(self, "Ошибка", "Подборку 'Все' нельзя удалить.")


    def playlist_selected(self, item):
        playlist_name = item.text()
        print(f"Selected playlist: {playlist_name}")
        if self.main_app:
            if playlist_name == "Все":
                self.main_app.load_kaomoji_for_playlist(None)  # Pass None for "Все"
            else:
                self.main_app.load_kaomoji_for_playlist(playlist_name)

class KaomojiApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kaomoji Helper")
        self.setGeometry(100, 100, 800, 550)
        self.db = KaomojiDatabase()
        self.sort_by_date = True
        self.search_tags = []
        self.show_favorites = False
        self.current_playlist = None

        self.kaomoji_data = []
        self.copied_kaomoji = []

        self.results_list = QListWidget()
        self.populate_kaomoji_list()

        self.add_button = QPushButton("Добавить Каомодзи")
        self.add_button.clicked.connect(self.add_kaomoji)

        self.sort_checkbox = QCheckBox("Сортировать по дате")
        self.sort_checkbox.setChecked(self.sort_by_date)
        self.sort_checkbox.stateChanged.connect(self.toggle_sort)

        self.search_tags_input = QLineEdit()
        self.search_tags_input.setPlaceholderText("Поиск по тегам (через запятую)")
        self.search_tags_input.returnPressed.connect(self.perform_search)

        self.favorites_button = QPushButton("Только избранные")
        self.favorites_button.setCheckable(True)
        self.favorites_button.clicked.connect(self.toggle_favorites)

        # Copy Buffer Section
        self.copied_kaomoji_text = QTextEdit()
        self.copied_kaomoji_text.setReadOnly(True)
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

        #Playlist Management
        self.playlist_management = PlaylistManagementWidget(main_app=self)

        # Main Layout with splitter
        main_layout = QHBoxLayout()

        # Left side (Kaomoji List and controls)
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.results_list)
        left_layout.addWidget(self.add_button)
        left_layout.addWidget(self.sort_checkbox)
        left_layout.addWidget(self.search_tags_input)
        left_layout.addWidget(self.favorites_button)
        left_layout.addLayout(copy_buffer_section_layout)

        # Splitter to separate Kaomoji list from playlist management
        splitter = QSplitter(Qt.Horizontal)

        left_widget = QWidget()
        left_widget.setLayout(left_layout)

        splitter.addWidget(left_widget)
        splitter.addWidget(self.playlist_management)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def load_kaomoji_data(self):
        search_tags = self.search_tags[:]
        show_favorites = self.show_favorites
        current_playlist = self.current_playlist

        print(f"Loading kaomoji data with search_tags: {search_tags}, show_favorites: {show_favorites}, current_playlist: {self.current_playlist}")

        kaomoji_list = self.db.get_all_kaomoji(sort_by_date=self.sort_by_date, search_tags=search_tags,
                                               show_favorites=show_favorites, current_playlist=current_playlist)

        print(f"Found {len(kaomoji_list)} kaomoji.")
        return kaomoji_list

    def load_kaomoji_for_playlist(self, playlist_name):
        self.current_playlist = playlist_name
        print(f"Loading kaomoji for playlist: {playlist_name}")
        self.kaomoji_data = self.load_kaomoji_data()
        self.populate_kaomoji_list()

    def perform_search(self):
        search_text = self.search_tags_input.text().strip()
        self.search_tags = [tag.strip() for tag in search_text.split(",") if tag.strip()]
        print(f"Performing search with tags: {self.search_tags}")
        self.kaomoji_data = self.load_kaomoji_data()
        self.populate_kaomoji_list()
        print(f"Search completed, kaomoji_data has {len(self.kaomoji_data)} items.")

    def toggle_sort(self, state):
        self.sort_by_date = state == Qt.Checked
        self.kaomoji_data = self.load_kaomoji_data()
        self.populate_kaomoji_list()

    def add_kaomoji(self):
        playlists = self.playlist_management.playlists
        dialog = AddKaomojiDialog(self, playlists=playlists)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            kaomoji, tags, playlist_name = dialog.get_kaomoji_data()
            if kaomoji:
                if self.db.add_kaomoji(kaomoji, tags, playlist_name):
                    self.kaomoji_data = self.load_kaomoji_data()
                    self.populate_kaomoji_list()
                    print(f"Added kaomoji: {kaomoji} with tags: {tags} to playlist: {playlist_name}")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось добавить каомодзи.")
            else:
                QMessageBox.warning(self, "Ошибка", "Каомодзи не может быть пустым!")

    def populate_kaomoji_list(self):
        print("Populating kaomoji list...")
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

            edit_tags_button = QPushButton("✏️")  # Use a pencil emoji
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

            # Favorite Button
            kaomoji_id = self.get_kaomoji_id(kaomoji)
            is_favorite = self.db.is_favorite(kaomoji_id)
            favorite_button = QPushButton("❤️" if is_favorite else "🤍")  # Heart emoji

            favorite_button.setStyleSheet("""
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
                    color: red;
                    font-size: 16px;
                }
            """)

            favorite_button.clicked.connect(lambda checked, k_id=kaomoji_id, k=kaomoji: self.toggle_favorite(k_id, k))
            layout.addWidget(favorite_button)

            kaomoji_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            layout.setAlignment(Qt.AlignRight)
            widget.setLayout(layout)
            item.setSizeHint(widget.sizeHint())

            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, widget)
        print("Kaomoji list populated.")
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

        print(f"Performing search with tags: {self.search_tags}, current playlist: {self.current_playlist}")

        self.kaomoji_data = self.load_kaomoji_data()
        self.populate_kaomoji_list()

        print(f"Search completed, kaomoji_data has {len(self.kaomoji_data)} items.")

    def get_kaomoji_id(self, kaomoji):
        return self.db.get_kaomoji_id(kaomoji)

    def toggle_favorite(self, kaomoji_id, kaomoji):
        if self.db.is_favorite(kaomoji_id):
            self.db.remove_from_favorites(kaomoji_id)
            print(f"Removed kaomoji {kaomoji} from favorites")
        else:
            self.db.add_to_favorites(kaomoji_id)
            print(f"Added kaomoji {kaomoji} to favorites")

        self.kaomoji_data = self.load_kaomoji_data()
        self.populate_kaomoji_list()

    def toggle_favorites(self):
        self.show_favorites = not self.show_favorites
        self.kaomoji_data = self.load_kaomoji_data()
        self.populate_kaomoji_list()

    def closeEvent(self, event):
        self.db.close()
        event.accept()

    def copy_kaomoji(self, kaomoji):
        self.copied_kaomoji.append(kaomoji)
        self.update_copied_kaomoji_text()
        print(f"Copied kaomoji: {kaomoji}")

    def update_copied_kaomoji_text(self):
        self.copied_kaomoji_text.setPlainText(" ".join(self.copied_kaomoji))

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(" ".join(self.copied_kaomoji))
        print("Copied to clipboard")

    def clear_copied_kaomoji(self):
        self.copied_kaomoji = []
        self.update_copied_kaomoji_text()
        print("Cleared copied kaomoji")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = KaomojiApp()
    # Prepopulate with some playlists if empty, before showing
    if not ex.playlist_management.playlists:
        ex.playlist_management.playlists = ["моя подборка 1", "моя подборка 2"]
        ex.playlist_management.playlist_list.addItems(ex.playlist_management.playlists) # Update UI List

    ex.show()
    sys.exit(app.exec_())
