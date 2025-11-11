"""Кастомные виджеты для GUI"""

import os
import pathlib
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTextEdit, QCheckBox, QProgressBar, 
    QGroupBox, QFormLayout, QFileDialog, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, pyqtSlot
from core.config import APP_DIR


class MainTab(QWidget):
    upload_requested = pyqtSignal(dict)
    log_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.platform_status = {}  # Для отслеживания статуса платформ
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()

        # Выбор файла
        file_layout = QHBoxLayout()
        self.file_label = QLineEdit()
        self.file_label.setReadOnly(True)
        btn_browse = QPushButton("Выбрать видео")
        btn_browse.clicked.connect(self.browse_video)
        file_layout.addWidget(QLabel("Файл:"))
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(btn_browse)
        layout.addLayout(file_layout)

        # Описание
        layout.addWidget(QLabel("Описание:"))
        self.desc_edit = QTextEdit()
        self.desc_edit.setFixedHeight(120)
        layout.addWidget(self.desc_edit)

        # Теги
        tag_layout = QHBoxLayout()
        self.tags_edit = QLineEdit()
        tag_layout.addWidget(QLabel("Теги:"))
        tag_layout.addWidget(self.tags_edit)
        layout.addLayout(tag_layout)

        # Платформы
        plat_group = QGroupBox("Платформы")
        plat_layout = QVBoxLayout()
        
        # Чекбоксы
        check_layout = QHBoxLayout()
        self.chk_youtube = QCheckBox("YouTube Shorts")
        self.chk_instagram = QCheckBox("Instagram Reels")
        self.chk_tiktok = QCheckBox("TikTok")
        check_layout.addWidget(self.chk_youtube)
        check_layout.addWidget(self.chk_instagram)
        check_layout.addWidget(self.chk_tiktok)
        
        # Статусы платформ
        status_layout = QVBoxLayout()
        self.youtube_status = QLabel("⏳ Ожидание")
        self.instagram_status = QLabel("⏳ Ожидание") 
        self.tiktok_status = QLabel("⏳ Ожидание")
        
        status_layout.addWidget(QLabel("Статусы:"))
        status_layout.addWidget(self.youtube_status)
        status_layout.addWidget(self.instagram_status)
        status_layout.addWidget(self.tiktok_status)
        
        plat_layout.addLayout(check_layout)
        plat_layout.addLayout(status_layout)
        plat_group.setLayout(plat_layout)
        layout.addWidget(plat_group)

        # Кнопка загрузки и прогресс
        h = QHBoxLayout()
        self.btn_upload = QPushButton("🔄 Загрузить на все платформы")
        self.btn_upload.clicked.connect(self.start_upload)
        self.progress = QProgressBar()
        h.addWidget(self.btn_upload)
        h.addWidget(self.progress)
        layout.addLayout(h)

        layout.addStretch()
        self.setLayout(layout)
        
        # Инициализируем статусы
        self.reset_platform_status()

    def reset_platform_status(self):
        """Сброс статусов платформ"""
        self.youtube_status.setText("⏳ Ожидание")
        self.instagram_status.setText("⏳ Ожидание")
        self.tiktok_status.setText("⏳ Ожидание")
        self.youtube_status.setStyleSheet("color: gray;")
        self.instagram_status.setStyleSheet("color: gray;")
        self.tiktok_status.setStyleSheet("color: gray;")

    def update_platform_status(self, platform, status):
        """Обновление статуса конкретной платформы"""
        status_widgets = {
            'youtube': self.youtube_status,
            'instagram': self.instagram_status, 
            'tiktok': self.tiktok_status
        }
        
        status_config = {
            'waiting': ("⏳ Ожидание", "gray"),
            'started': ("🚀 Загружается...", "blue"),
            'completed': ("✅ Завершено", "green"),
            'error': ("❌ Ошибка", "red")
        }
        
        if platform in status_widgets and status in status_config:
            text, color = status_config[status]
            status_widgets[platform].setText(text)
            status_widgets[platform].setStyleSheet(f"color: {color}; font-weight: bold;")

    def browse_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "Выберите видео", 
            str(pathlib.Path.home()),
            "Видео (*.mp4 *.mov *.mkv *.webm);;Все файлы (*)"
        )
        if path:
            self.file_label.setText(path)

    def start_upload(self):
        video = self.file_label.text().strip()
        if not video or not os.path.exists(video):
            QMessageBox.critical(self, "Ошибка", "Выберите существующий видеофайл.")
            return

        platforms = []
        if self.chk_youtube.isChecked(): 
            platforms.append("youtube")
        if self.chk_instagram.isChecked(): 
            platforms.append("instagram")
        if self.chk_tiktok.isChecked(): 
            platforms.append("tiktok")
        
        if not platforms:
            QMessageBox.warning(self, "Платформа не выбрана", "Выберите хотя бы одну платформу.")
            return

        description = self.desc_edit.toPlainText().strip()
        tags = self.tags_edit.text().strip()

        task_data = {
            "video": video, 
            "description": description, 
            "tags": tags, 
            "platforms": platforms
        }
        
        self.upload_requested.emit(task_data)


class CredentialsTab(QWidget):
    credentials_saved = pyqtSignal(dict)
    
    def __init__(self, initial_creds=None):
        super().__init__()
        self.creds = initial_creds or {}
        self.setup_ui()
        self.load_initial_creds()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        # YouTube
        self.yt_client_secrets = QLineEdit()
        self.yt_token_file = QLineEdit(os.path.join(APP_DIR, "yt_token.json"))
        
        btn_browse_client_secrets = QPushButton("Выбрать")
        btn_browse_client_secrets.clicked.connect(self.browse_client_secrets)
        
        yt_secrets_layout = QHBoxLayout()
        yt_secrets_layout.addWidget(self.yt_client_secrets)
        yt_secrets_layout.addWidget(btn_browse_client_secrets)
        
        form.addRow("YouTube client_secrets.json:", yt_secrets_layout)
        form.addRow("YouTube token.json:", self.yt_token_file)

        # TikTok
        self.tt_cookies_file = QLineEdit()
        btn_browse_cookies = QPushButton("Выбрать cookies (txt/json)")
        btn_browse_cookies.clicked.connect(self.browse_cookies)
        
        cookies_layout = QHBoxLayout()
        cookies_layout.addWidget(self.tt_cookies_file)
        cookies_layout.addWidget(btn_browse_cookies)
        form.addRow("TikTok cookies:", cookies_layout)

        # Instagram
        self.ig_username = QLineEdit()
        self.ig_password = QLineEdit()
        self.ig_password.setEchoMode(QLineEdit.EchoMode.Password)
        
        form.addRow("Instagram Username:", self.ig_username)
        form.addRow("Instagram Password:", self.ig_password)

        # Кнопка сохранения
        btn_save = QPushButton("Сохранить учетные данные")
        btn_save.clicked.connect(self.save_credentials)

        layout.addLayout(form)
        layout.addWidget(btn_save)
        layout.addStretch()
        self.setLayout(layout)

    def load_initial_creds(self):
        """Загрузка начальных учетных данных"""
        # YouTube
        yt_creds = self.creds.get("youtube", {})
        self.yt_client_secrets.setText(yt_creds.get("client_secrets_file", ""))
        self.yt_token_file.setText(yt_creds.get("token_file", os.path.join(APP_DIR, "yt_token.json")))
        
        # TikTok
        tt_creds = self.creds.get("tiktok", {})
        self.tt_cookies_file.setText(tt_creds.get("cookies_file", ""))
        
        # Instagram
        ig_creds = self.creds.get("instagram", {})
        self.ig_username.setText(ig_creds.get("username", ""))
        self.ig_password.setText(ig_creds.get("password", ""))

    def browse_client_secrets(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "Выберите client_secrets.json", 
            str(pathlib.Path.home()),
            "JSON files (*.json);;All files (*)"
        )
        if path:
            self.yt_client_secrets.setText(path)

    def browse_cookies(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "Выберите cookies файл", 
            str(pathlib.Path.home()),
            "Cookies (*.txt *.json);;All files (*)"
        )
        if path:
            self.tt_cookies_file.setText(path)

    def save_credentials(self):
        """Сохранение учетных данных"""
        new_creds = {
            "youtube": {
                "client_secrets_file": self.yt_client_secrets.text().strip(),
                "token_file": self.yt_token_file.text().strip()
            },
            "tiktok": {
                "cookies_file": self.tt_cookies_file.text().strip()
            },
            "instagram": {
                "username": self.ig_username.text().strip(),
                "password": self.ig_password.text().strip()
            }
        }
        
        # Валидация
        errors = self.validate_credentials(new_creds)
        if errors:
            QMessageBox.warning(self, "Ошибки валидации", "\n".join(errors))
            return
        
        self.credentials_saved.emit(new_creds)

    def validate_credentials(self, creds):
        """Валидация учетных данных"""
        errors = []
        
        # YouTube
        yt_secrets = creds["youtube"]["client_secrets_file"]
        if yt_secrets and not os.path.exists(yt_secrets):
            errors.append("Файл client_secrets.json для YouTube не найден")
        
        # TikTok
        tt_cookies = creds["tiktok"]["cookies_file"]
        if tt_cookies and not os.path.exists(tt_cookies):
            errors.append("Файл cookies для TikTok не найден")
        
        # Instagram
        ig_username = creds["instagram"]["username"]
        ig_password = creds["instagram"]["password"]
        if (ig_username and not ig_password) or (ig_password and not ig_username):
            errors.append("Для Instagram необходимо указать и логин, и пароль")
        
        return errors


class LogsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Кнопки управления логами
        btn_layout = QHBoxLayout()
        btn_clear = QPushButton("Очистить логи")
        btn_clear.clicked.connect(self.clear_logs)
        btn_save = QPushButton("Сохранить логи в файл")
        btn_save.clicked.connect(self.save_logs)
        
        btn_layout.addWidget(btn_clear)
        btn_layout.addWidget(btn_save)
        btn_layout.addStretch()
        
        # Текстовое поле для логов
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        
        layout.addLayout(btn_layout)
        layout.addWidget(self.log_text)
        self.setLayout(layout)

    @pyqtSlot(str)
    def append_log(self, text):
        """Добавление текста в логи"""
        self.log_text.append(text)
        # Автопрокрутка к новому сообщению
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def clear_logs(self):
        """Очистка логов"""
        self.log_text.clear()

    def save_logs(self):
        """Сохранение логов в файл"""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить логи",
            str(pathlib.Path.home() / "uploader_logs.txt"),
            "Text files (*.txt);;All files (*)"
        )
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "Успех", "Логи сохранены успешно")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить логи: {str(e)}")