from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton,
                             QInputDialog, QMessageBox)


class PlaylistManagementWidget(QWidget):
    def __init__(self, parent=None, main_app=None):
        super().__init__(parent)
        self.playlists = ["моя подборка 1", "моя подборка 2"]
        self.playlist_list = QListWidget()
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
            if playlist_name not in self.playlists:
                self.playlists.append(playlist_name)
                self.playlist_list.addItem(playlist_name)
            else:
                QMessageBox.warning(self, "Ошибка", "Подборка с таким именем уже существует.")

    def delete_playlist(self):
        selected_item = self.playlist_list.currentItem()
        if selected_item:
            playlist_name = selected_item.text()
            reply = QMessageBox.question(self, 'Удаление',
                                         f"Удалить подборку '{playlist_name}'?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.playlists.remove(playlist_name)
                self.playlist_list.takeItem(self.playlist_list.row(selected_item))
                # Обновляем данные в базе
                if self.main_app:
                    self.main_app.load_kaomoji_for_playlist(None)

    def playlist_selected(self, item):
        playlist_name = item.text()
        print(f"Selected playlist: {playlist_name}")
        if self.main_app:
            self.main_app.load_kaomoji_for_playlist(playlist_name)