from PyQt6.QtCore import QThread, pyqtSignal
from uploaders.youtube_uploader import YouTubeUploader
from uploaders.tiktok_uploader import TikTokUploader
from uploaders.instagram_uploader import InstagramUploader


class UploadWorker(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished_signal = pyqtSignal(dict)
    
    def __init__(self, task):
        super().__init__()
        self.task = task
        self.uploaders = {
            'youtube': YouTubeUploader(),
            'tiktok': TikTokUploader(),
            'instagram': InstagramUploader()
        }
    
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

        for platform in platforms:
            if platform in self.uploaders:
                self.log.emit(f"Загрузка на {platform.capitalize()}...")
                try:
                    uploader = self.uploaders[platform]
                    r = uploader.upload(video, desc, tags, creds.get(platform, {}))
                    result[platform] = {"ok": True, "resp": r}
                    self.log.emit(f"{platform.capitalize()}: успешно.")
                except Exception as e:
                    result[platform] = {"ok": False, "error": str(e)}
                    self.log.emit(f"{platform.capitalize()}: ошибка: {e}")
                
                done += 1
                self.progress.emit(int(done / total * 100))

        if total == 0:
            self.progress.emit(100)

        self.log.emit("Готово.")
        self.finished_signal.emit(result)