import json
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QMessageBox, QApplication
)
from PyQt6.QtCore import pyqtSignal

from core.config import Config
from core.worker import UploadWorker
from .widgets import MainTab, CredentialsTab, LogsTab


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Uploader — YouTube / TikTok / Instagram")
        self.resize(980, 680)
        self.config = Config()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        tabs = QTabWidget()
        
        # Создаем вкладки
        self.main_tab = MainTab()
        self.creds_tab = CredentialsTab(self.config.creds)
        self.logs_tab = LogsTab()
        
        # Подключаем сигналы
        self.main_tab.upload_requested.connect(self.handle_upload)
        self.main_tab.log_signal.connect(self.logs_tab.append_log)
        self.creds_tab.credentials_saved.connect(self.on_credentials_saved)
        
        tabs.addTab(self.main_tab, "Загрузка")
        tabs.addTab(self.creds_tab, "Учётные данные")
        tabs.addTab(self.logs_tab, "Логи")
        
        layout.addWidget(tabs)
        self.setLayout(layout)
    
    def handle_upload(self, task_data):
        """Обработка начала загрузки"""
        task_data["creds"] = self.config.creds
        
        self.worker = UploadWorker(task_data)
        self.worker.progress.connect(self.main_tab.progress.setValue)
        self.worker.log.connect(self.logs_tab.append_log)
        self.worker.finished_signal.connect(self.on_upload_finished)
        self.main_tab.btn_upload.setEnabled(False)
        self.worker.start()
    
    def on_upload_finished(self, result):
        """Обработка завершения загрузки"""
        self.main_tab.btn_upload.setEnabled(True)
        self.logs_tab.append_log(json.dumps(result, ensure_ascii=False, indent=2))
        QApplication.beep()  # системный звуковой сигнал
    
    def on_credentials_saved(self, new_creds):
        """Обновление конфигурации при сохранении учетных данных"""
        self.config.creds = new_creds
        self.config.save_creds()
        self.show_message("Успех", "Учетные данные сохранены")
    
    def show_message(self, title, message, message_type=QMessageBox.Icon.Information):
        msg = QMessageBox()
        msg.setIcon(message_type)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec()