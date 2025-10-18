import os
import mimetypes

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:
    InstalledAppFlow = None
    build = None
    MediaFileUpload = None

from .base import BaseUploader

SCOPES_YOUTUBE = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]


class YouTubeUploader(BaseUploader):
    def upload(self, video_path, description, tags, credentials):
        if InstalledAppFlow is None:
            raise RuntimeError("google libraries not installed. pip install google-auth-oauthlib google-api-python-client")
        
        client_secrets = credentials.get("client_secrets_file")
        token_file = credentials.get("token_file", os.path.join(os.path.expanduser("~"), ".video_uploader", "yt_token.json"))
        
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
    
    def validate_credentials(self, credentials):
        client_secrets = credentials.get("client_secrets_file")
        if not client_secrets or not os.path.exists(client_secrets):
            return False, "Client secrets file not found"
        return True, "OK"