from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition
from PyQt6.QtWidgets import QApplication
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from uploaders.youtube_uploader import YouTubeUploader
from uploaders.tiktok_uploader import TikTokUploader
from uploaders.instagram_uploader import InstagramUploader


class ParallelUploadWorker(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished_signal = pyqtSignal(dict)
    platform_progress = pyqtSignal(str, str)  # platform, status
    
    def __init__(self, task):
        super().__init__()
        self.task = task
        self.uploaders = {
            'youtube': YouTubeUploader(),
            'tiktok': TikTokUploader(),
            'instagram': InstagramUploader()
        }
        self.mutex = QMutex()
        self.completed_count = 0
        self.results = {}
        
    def run(self):
        result = {}
        self.log.emit("🚀 Старт параллельной загрузки...")
        
        video = self.task["video"]
        desc = self.task["description"]
        tags = self.task["tags"]
        platforms = self.task["platforms"]
        creds = self.task["creds"]
        
        total = len(platforms)
        
        if total == 0:
            self.progress.emit(100)
            self.finished_signal.emit({})
            return

        # Используем ThreadPoolExecutor для параллельного выполнения
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Запускаем все загрузки одновременно
            future_to_platform = {}
            
            for platform in platforms:
                if platform in self.uploaders:
                    future = executor.submit(
                        self.upload_to_platform, 
                        platform, video, desc, tags, creds.get(platform, {})
                    )
                    future_to_platform[future] = platform
            
            # Обрабатываем завершённые задачи по мере их выполнения
            for future in as_completed(future_to_platform):
                platform = future_to_platform[future]
                try:
                    platform_result = future.result()
                    self.results[platform] = platform_result
                except Exception as e:
                    self.results[platform] = {"ok": False, "error": str(e)}
                
                self.mutex.lock()
                self.completed_count += 1
                progress = int(self.completed_count / total * 100)
                self.mutex.unlock()
                
                self.progress.emit(progress)
                self.log.emit(f"✅ {platform.capitalize()}: завершено")

        self.log.emit("🎉 Все загрузки завершены!")
        self.finished_signal.emit(self.results)
    
    def upload_to_platform(self, platform, video_path, description, tags, credentials):
        """Метод для загрузки на конкретную платформу (выполняется в отдельном потоке)"""
        
        platform_name = platform.capitalize()
        self.platform_progress.emit(platform, "started")
        self.log.emit(f"⏳ {platform_name}: начинается загрузка...")
        
        try:
            uploader = self.uploaders[platform]
            
            # Для TikTok передаём функцию логирования
            if platform == 'tiktok':
                result = uploader.upload(video_path, description, tags, credentials, log_fn=self.log.emit)
            else:
                result = uploader.upload(video_path, description, tags, credentials)
            
            self.platform_progress.emit(platform, "completed")
            self.log.emit(f"✅ {platform_name}: успешно загружено!")
            return {"ok": True, "resp": result}
            
        except Exception as e:
            self.platform_progress.emit(platform, "error")
            self.log.emit(f"❌ {platform_name}: ошибка - {str(e)}")
            return {"ok": False, "error": str(e)}