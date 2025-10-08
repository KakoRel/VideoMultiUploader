"""
uploader.py — GUI-приложение для загрузки видео в YouTube Shorts, Instagram Reels и TikTok.

"""

import sys
import os
import json
import mimetypes
import pathlib

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QFileDialog,
    QTextEdit, QVBoxLayout, QHBoxLayout, QCheckBox, QProgressBar, QMessageBox,
    QTabWidget, QFormLayout, QGroupBox
)
from PyQt6.QtCore import QThread, pyqtSignal

# TikTok uploader
try:
    from tiktok_uploader.upload import upload_video
    from tiktok_uploader.auth import AuthBackend
except Exception:
    upload_video = None
    AuthBackend = None

# Instagram (instagrapi)
try:
    from instagrapi import Client
except Exception:
    Client = None

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except Exception:
    InstalledAppFlow = None
    build = None
    MediaFileUpload = None

APP_DIR = os.path.join(pathlib.Path.home(), ".video_uploader")
os.makedirs(APP_DIR, exist_ok=True)
CRED_STORE = os.path.join(APP_DIR, "creds.json")
IG_SESSION = os.path.join(APP_DIR, "session.json")
SCOPES_YOUTUBE = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]


def load_creds():
    if os.path.exists(CRED_STORE):
        with open(CRED_STORE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}


def save_creds(data):
    with open(CRED_STORE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------------------
# YouTube Shorts
# ---------------------------

def upload_youtube(video_path, description, tags, yt_creds_config):
    if InstalledAppFlow is None:
        raise RuntimeError("google libraries not installed. pip install google-auth-oauthlib google-api-python-client")
    client_secrets = yt_creds_config.get("client_secrets_file") if yt_creds_config else None
    token_file = yt_creds_config.get("token_file") if yt_creds_config else os.path.join(APP_DIR, "yt_token.json")
    if not client_secrets or not os.path.exists(client_secrets):
        raise FileNotFoundError("OAuth client_secrets.json для YouTube не найден.")
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES_YOUTUBE)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets, SCOPES_YOUTUBE)
            creds = flow.run_local_server(port=0)
        with open(token_file, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
    body = {
        "snippet": {
            "title": (description[:100] or "Shorts upload").strip(),
            "description": description,
            "tags": tags.split() if tags else []
        },
        "status": {"privacyStatus": "public"}
    }
    mime_type, _ = mimetypes.guess_type(video_path)
    if not mime_type:
        mime_type = "video/*"
    media = MediaFileUpload(video_path, chunksize=1048576, resumable=True, mimetype=mime_type)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while True:
        status, resp = request.next_chunk()
        if resp:
            response = resp
            break
    return response


# ---------------------------
# TikTok
# ---------------------------

def upload_tiktok(video_path, description, tags, tt_creds, log_fn=print):
    if upload_video is None or AuthBackend is None:
        raise RuntimeError("tiktok-uploader не установлен. pip install tiktok-uploader")

    cookies_file = tt_creds.get("cookies_file")
    if not cookies_file or not os.path.exists(cookies_file):
        raise RuntimeError("Не задан файл cookies для TikTok или файл не существует.")

    # Если надо много видео в ТТ загрузить авторизоваться так:
    # auth = AuthBackend(cookies=cookies_file)
    
    # Формируем текст с описанием и тегами
    text = f"{description}\n{tags}" if tags else description
    
    log_fn(f"TikTok: загружаем {video_path} с cookies {cookies_file}")
    
    # Прямой вызов upload_video как в рабочем примере
    result = upload_video(
        filename=video_path,
        description=text,
        cookies=cookies_file,
        #headless=True
    )
    
    return {"ok": True, "resp": str(result)}


# ---------------------------
# Instagram Reels (instagrapi)
# ---------------------------

def upload_instagram(video_path, description, tags, ig_creds):
    if Client is None:
        raise RuntimeError("instagrapi не установлен. Установите: pip install instagrapi")

    cl = Client()

    username = ig_creds.get("username")
    password = ig_creds.get("password")

    if not username or not password:
        raise RuntimeError("Введите Instagram username и password в настройках.")

    # Пробуем использовать сохранённую сессию
    if os.path.exists(IG_SESSION):
        try:
            cl.load_settings(IG_SESSION)
            cl.login(username, password)
        except Exception:
            cl = Client()
            cl.login(username, password)
            cl.dump_settings(IG_SESSION)
    else:
        cl.login(username, password)
        cl.dump_settings(IG_SESSION)

    caption = f"{description}\n{tags}" if tags else description
    media = cl.clip_upload(video_path, caption)
    return {"ok": True, "resp": str(media.dict())}


# ---------------------------
# Worker
# ---------------------------

class UploadWorker(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished_signal = pyqtSignal(dict)

    def __init__(self, task):
        super().__init__()
        self.task = task

    def run(self):
        result = {}
        self.log.emit("Старт загрузки...")
        video = self.task["video"]
        desc = self.task["description"]
        tags = self.task["tags"]
        platforms = self.task["platforms"]
        creds = self.task["creds"]
        total = len(platforms)
        done = 0

        if "youtube" in platforms:
            self.log.emit("Загрузка на YouTube...")
            try:
                r = upload_youtube(video, desc, tags, creds.get("youtube"))
                result["youtube"] = {"ok": True, "resp": r}
                self.log.emit("YouTube: успешно.")
            except Exception as e:
                result["youtube"] = {"ok": False, "error": str(e)}
                self.log.emit(f"YouTube: ошибка: {e}")
            done += 1
            self.progress.emit(int(done / total * 100))

        if "tiktok" in platforms:
            self.log.emit("Загрузка на TikTok...")
            try:
                r = upload_tiktok(video, desc, tags, creds.get("tiktok"), log_fn=self.log.emit)
                result["tiktok"] = {"ok": True, "resp": r}
                self.log.emit("TikTok: успешно.")
            except Exception as e:
                result["tiktok"] = {"ok": False, "error": str(e)}
                self.log.emit(f"TikTok: ошибка: {e}")
            done += 1
            self.progress.emit(int(done / total * 100))

        if "instagram" in platforms:
            self.log.emit("Загрузка на Instagram Reels...")
            try:
                r = upload_instagram(video, desc, tags, creds.get("instagram", {}))
                result["instagram"] = {"ok": True, "resp": r}
                self.log.emit("Instagram: успешно.")
            except Exception as e:
                result["instagram"] = {"ok": False, "error": str(e)}
                self.log.emit(f"Instagram: ошибка: {e}")
            done += 1
            self.progress.emit(int(done / total * 100))

        if total == 0:
            self.progress.emit(100)

        self.log.emit("Готово.")
        self.finished_signal.emit(result)


# ---------------------------
# GUI
# ---------------------------

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Uploader — YouTube / TikTok / Instagram")
        self.resize(980, 680)
        self.creds = load_creds()
        self.creds.setdefault("tiktok", {})
        self.creds.setdefault("instagram", {})
        self.creds.setdefault("youtube", {})
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        tabs = QTabWidget()
        tabs.addTab(self.tab_main_ui(), "Загрузка")
        tabs.addTab(self.tab_creds_ui(), "Учётные данные")
        tabs.addTab(self.tab_logs_ui(), "Логи")
        layout.addWidget(tabs)
        self.setLayout(layout)

    def tab_main_ui(self):
        w = QWidget()
        v = QVBoxLayout()

        file_layout = QHBoxLayout()
        self.file_label = QLineEdit(); self.file_label.setReadOnly(True)
        btn_browse = QPushButton("Выбрать видео"); btn_browse.clicked.connect(self.browse_video)
        file_layout.addWidget(QLabel("Файл:")); file_layout.addWidget(self.file_label); file_layout.addWidget(btn_browse)
        v.addLayout(file_layout)

        v.addWidget(QLabel("Описание:"))
        self.desc_edit = QTextEdit(); self.desc_edit.setFixedHeight(120); v.addWidget(self.desc_edit)

        tag_layout = QHBoxLayout()
        self.tags_edit = QLineEdit()
        tag_layout.addWidget(QLabel("Теги:")); tag_layout.addWidget(self.tags_edit); v.addLayout(tag_layout)

        plat_group = QGroupBox("Платформы"); plat_layout = QHBoxLayout()
        self.chk_youtube = QCheckBox("YouTube Shorts")
        self.chk_instagram = QCheckBox("Instagram Reels")
        self.chk_tiktok = QCheckBox("TikTok")
        plat_layout.addWidget(self.chk_youtube); plat_layout.addWidget(self.chk_instagram); plat_layout.addWidget(self.chk_tiktok)
        plat_group.setLayout(plat_layout); v.addWidget(plat_group)

        h = QHBoxLayout()
        self.btn_upload = QPushButton("Загрузить"); self.btn_upload.clicked.connect(self.start_upload)
        self.progress = QProgressBar()
        h.addWidget(self.btn_upload); h.addWidget(self.progress); v.addLayout(h)

        w.setLayout(v)
        return w

    def tab_creds_ui(self):
        w = QWidget()
        layout = QVBoxLayout()
        form = QFormLayout()

        # YouTube
        self.yt_client_secrets = QLineEdit(self.creds.get("youtube", {}).get("client_secrets_file", ""))
        self.yt_token_file = QLineEdit(self.creds.get("youtube", {}).get("token_file", os.path.join(APP_DIR, "yt_token.json")))
        form.addRow("YouTube client_secrets.json:", self.yt_client_secrets)
        form.addRow("YouTube token.json:", self.yt_token_file)

        # TikTok
        self.tt_cookies_file = QLineEdit(self.creds.get("tiktok", {}).get("cookies_file", ""))
        btn_browse_cookies = QPushButton("Выбрать cookies (txt/json)")
        btn_browse_cookies.clicked.connect(self.browse_cookies)
        cookies_layout = QHBoxLayout(); cookies_layout.addWidget(self.tt_cookies_file); cookies_layout.addWidget(btn_browse_cookies)
        form.addRow("TikTok cookies:", cookies_layout)

        # Instagram
        self.ig_username = QLineEdit(self.creds.get("instagram", {}).get("username", ""))
        self.ig_password = QLineEdit(self.creds.get("instagram", {}).get("password", ""))
        self.ig_password.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Instagram Username:", self.ig_username)
        form.addRow("Instagram Password:", self.ig_password)

        btn_save = QPushButton("Сохранить креденшалы")
        btn_save.clicked.connect(self.save_credentials)

        layout.addLayout(form)
        layout.addWidget(btn_save)
        w.setLayout(layout)
        return w

    def tab_logs_ui(self):
        w = QWidget()
        v = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        v.addWidget(self.log_text)
        w.setLayout(v)
        self.vlogs = self.log_text
        return w

    def browse_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите видео", str(pathlib.Path.home()),
                                              "Видео (*.mp4 *.mov *.mkv *.webm);;Все файлы (*)")
        if path:
            self.file_label.setText(path)

    def browse_cookies(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите cookies (txt/json)", str(pathlib.Path.home()),
                                              "Cookies (*.txt *.json)")
        if path:
            self.tt_cookies_file.setText(path)

    def save_credentials(self):
        self.creds["youtube"] = {
            "client_secrets_file": self.yt_client_secrets.text().strip(),
            "token_file": self.yt_token_file.text().strip()
        }
        self.creds["tiktok"] = {"cookies_file": self.tt_cookies_file.text().strip()}
        self.creds["instagram"] = {
            "username": self.ig_username.text().strip(),
            "password": self.ig_password.text().strip()
        }
        save_creds(self.creds)
        QMessageBox.information(self, "ОК", "Креденшалы сохранены")

    def append_log(self, text):
        if hasattr(self, "vlogs"):
            self.vlogs.append(text)
        else:
            print(text)

    def start_upload(self):
        video = self.file_label.text().strip()
        if not video or not os.path.exists(video):
            QMessageBox.critical(self, "Ошибка", "Выберите существующий видеофайл.")
            return

        platforms = []
        if self.chk_youtube.isChecked(): platforms.append("youtube")
        if self.chk_instagram.isChecked(): platforms.append("instagram")
        if self.chk_tiktok.isChecked(): platforms.append("tiktok")
        if not platforms:
            QMessageBox.warning(self, "Платформа не выбрана", "Выберите хотя бы одну платформу.")
            return

        description = self.desc_edit.toPlainText().strip()
        tags = self.tags_edit.text().strip()

        task = {"video": video, "description": description, "tags": tags, "platforms": platforms, "creds": self.creds}
        self.worker = UploadWorker(task)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.log.connect(self.append_log)
        self.worker.finished_signal.connect(self.on_finished)
        self.btn_upload.setEnabled(False)
        self.worker.start()

    def on_finished(self, result):
        self.btn_upload.setEnabled(True)
        self.append_log(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
