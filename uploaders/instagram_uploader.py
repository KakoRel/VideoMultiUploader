import os

try:
    from instagrapi import Client
except ImportError:
    Client = None

from .base import BaseUploader

IG_SESSION = os.path.join(os.path.expanduser("~"), ".video_uploader", "session.json")


class InstagramUploader(BaseUploader):
    def upload(self, video_path, description, tags, credentials):
        if Client is None:
            raise RuntimeError("instagrapi не установлен. Установите: pip install instagrapi")

        cl = Client()

        username = credentials.get("username")
        password = credentials.get("password")

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
        return {"ok": True, "resp": str(media.model_dump())}
    
    def validate_credentials(self, credentials):
        username = credentials.get("username")
        password = credentials.get("password")
        if not username or not password:
            return False, "Username or password missing"
        return True, "OK"