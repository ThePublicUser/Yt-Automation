import os
import pickle
import base64
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

load_dotenv()

# -------------------------------
# Configuration
# -------------------------------
CLIENT_SECRETS_FILE = os.getenv("CLIENT_SECRET_JSON", "client_secrets.json")
CLIENT_SECRET_PICKLE_BASE64 = os.getenv("CLIENT_SECRET_PICKLE_BASE64")
BASE64_FILE_PATH = "token_base64.txt"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# -------------------------------
# Authentication
# -------------------------------
def get_authenticated_service():
    creds = None

    try:
        # 1️⃣ Load credentials from local base64 file (optional)
        if os.path.exists(BASE64_FILE_PATH):
            with open(BASE64_FILE_PATH, "r") as f:
                base64_str = f.read().strip()
                pickle_bytes = base64.b64decode(base64_str)
                creds = pickle.loads(pickle_bytes)
                print("✅ Loaded credentials from base64 file")

        # 2️⃣ Load from environment variable (GitHub secret)
        elif CLIENT_SECRET_PICKLE_BASE64:
            pickle_bytes = base64.b64decode(CLIENT_SECRET_PICKLE_BASE64)
            creds = pickle.loads(pickle_bytes)
            print("✅ Loaded credentials from env variable")

        # 3️⃣ Load from local token.pickle
        elif os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as f:
                creds = pickle.load(f)
                print("✅ Loaded credentials from token.pickle")

        else:
            raise Exception("❌ No credentials found. Please generate token.pickle locally.")

        # Refresh expired token
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing token...")
            creds.refresh(Request())
            print("✅ Token refreshed successfully")

        # Validate credentials
        if not creds or not creds.valid:
            raise Exception("❌ Credentials invalid after refresh")

        # Build YouTube service
        youtube = build("youtube", "v3", credentials=creds)
        return youtube

    except Exception as e:
        print("🚨 AUTHENTICATION FAILED")
        print(e)
        return None

# -------------------------------
# Upload Video
# -------------------------------
def upload_video_to_yt(file_path, title, description="", tags=None,
                       category_id="22", privacy_status="private",
                       made_for_kids=False):

    try:
        # Check if video exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found: {file_path}")

        youtube = get_authenticated_service()
        if youtube is None:
            raise Exception("YouTube service not initialized")

        # Build request body
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or [],
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": made_for_kids
            }
        }

        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        print("🚀 Starting upload...")
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploading... {int(status.progress() * 100)}%")

        print(f"\n✅ Video uploaded: https://www.youtube.com/watch?v={response['id']}")
        return response

    except HttpError as e:
        print("🚨 YOUTUBE API ERROR:")
        print(e)
        return None
    except Exception as e:
        print("🚨 UPLOAD FAILED:")
        print(e)
        return None

