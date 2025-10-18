import os
import json
import pathlib

APP_DIR = os.path.join(pathlib.Path.home(), ".video_uploader")
os.makedirs(APP_DIR, exist_ok=True)
CRED_STORE = os.path.join(APP_DIR, "creds.json")
IG_SESSION = os.path.join(APP_DIR, "session.json")

class Config:
    def __init__(self):
        self.creds = self.load_creds()
    
    def load_creds(self):
        if os.path.exists(CRED_STORE):
            with open(CRED_STORE, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except:
                    return {}
        return {}
    
    def save_creds(self):
        with open(CRED_STORE, "w", encoding="utf-8") as f:
            json.dump(self.creds, f, indent=2, ensure_ascii=False)
    
    def get_platform_creds(self, platform):
        return self.creds.get(platform, {})
    
    def set_platform_creds(self, platform, creds_data):
        self.creds[platform] = creds_data
        self.save_creds()
