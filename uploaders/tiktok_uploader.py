import os

try:
    from tiktok_uploader.upload import upload_video
    from tiktok_uploader.auth import AuthBackend
except ImportError:
    upload_video = None
    AuthBackend = None

from .base import BaseUploader


class TikTokUploader(BaseUploader):
    def upload(self, video_path, description, tags, credentials, log_fn=print):
        if upload_video is None or AuthBackend is None:
            raise RuntimeError("tiktok-uploader не установлен. pip install tiktok-uploader")

        cookies_file = credentials.get("cookies_file")
        if not cookies_file or not os.path.exists(cookies_file):
            raise RuntimeError("Не задан файл cookies для TikTok или файл не существует.")

        # Формируем текст с описанием и тегами
        text = f"{description}" if tags else description
        
        if log_fn:
            log_fn(f"TikTok: загружаем {video_path} с cookies {cookies_file}")
        
        # Прямой вызов upload_video как в рабочем примере
        result = upload_video(
            filename=video_path,
            description=text,
            cookies=cookies_file,
            #headless=True
        )
        
        return {"ok": True, "resp": str(result)}
    
    def validate_credentials(self, credentials):
        cookies_file = credentials.get("cookies_file")
        if not cookies_file or not os.path.exists(cookies_file):
            return False, "Cookies file not found"
        return True, "OK"