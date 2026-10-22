import os
import re
import json
import io
import uuid
import logging
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger("google_drive")

# Google Drive regex patterns
DRIVE_PATTERNS = [
    r"drive\.google\.com\/file\/d\/([a-zA-Z0-9_-]+)",
    r"drive\.google\.com\/open\?id=([a-zA-Z0-9_-]+)",
    r"drive\.google\.com\/uc\?(?:export=view&)?id=([a-zA-Z0-9_-]+)",
    r"drive\.google\.com\/thumbnail\?id=([a-zA-Z0-9_-]+)",
    r"lh3\.googleusercontent\.com\/d\/([a-zA-Z0-9_-]+)",
]

DEFAULT_GOOGLE_DRIVE_FOLDER_ID = "1jUDReWFnEGxMZplQwHRVXIsZGJ5a85Qi"

def extract_google_drive_folder_id(url_or_id: Optional[str]) -> Optional[str]:
    """
    Extracts the folder ID from any Google Drive folder link or returns the raw ID.
    Supports:
      - https://drive.google.com/drive/folders/1jUDReWFnEGxMZplQwHRVXIsZGJ5a85Qi?usp=sharing
      - https://drive.google.com/drive/u/0/folders/1jUDReWFnEGxMZplQwHRVXIsZGJ5a85Qi
      - 1jUDReWFnEGxMZplQwHRVXIsZGJ5a85Qi
    """
    if not url_or_id or not isinstance(url_or_id, str):
        return None
    url_or_id = url_or_id.strip()
    match = re.search(r"folders\/([a-zA-Z0-9_-]+)", url_or_id)
    if match:
        return match.group(1)
    if re.fullmatch(r"[a-zA-Z0-9_-]+", url_or_id):
        return url_or_id
    return url_or_id

def extract_google_drive_id(url: str) -> Optional[str]:
    """
    Extracts the file ID from any Google Drive link.
    Returns None if not a recognized Google Drive URL.
    """
    if not url or not isinstance(url, str):
        return None
    url = url.strip()
    for pattern in DRIVE_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def format_direct_google_drive_url(file_id: str) -> str:
    """
    Returns the direct CDN image URL for a Google Drive file ID.
    Works natively in Next.js Image and browser <img> tags.
    """
    return f"https://lh3.googleusercontent.com/d/{file_id}"

def normalize_image_url(url: str) -> str:
    """
    Normalizes any image URL. If it's a Google Drive link, converts it
    to the direct image stream URL: https://lh3.googleusercontent.com/d/<ID>.
    Otherwise returns the original URL.
    """
    if not url or not isinstance(url, str):
        return url
    file_id = extract_google_drive_id(url)
    if file_id:
        return format_direct_google_drive_url(file_id)
    return url.strip()

def get_google_drive_credentials():
    """
    Retrieves Google credentials from either:
    1. GOOGLE_APPLICATION_CREDENTIALS environment variable (file path)
    2. google_service_account.json in the current working directory or backend root
    3. GOOGLE_SERVICE_ACCOUNT_JSON environment variable (full JSON string)
    4. Individual env vars: GOOGLE_DRIVE_CLIENT_EMAIL and GOOGLE_DRIVE_PRIVATE_KEY
    """
    try:
        from google.oauth2 import service_account
    except ImportError:
        logger.warning("[Google Drive] google.oauth2 not installed.")
        return None

    SCOPES = ["https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    # 1. Path from GOOGLE_APPLICATION_CREDENTIALS or standard file names
    cred_paths = [
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        os.path.join(os.getcwd(), "google_service_account.json"),
        os.path.join(os.path.dirname(__file__), "..", "google_service_account.json"),
        os.path.join(os.path.dirname(__file__), "..", "..", "google_service_account.json"),
    ]

    for path in cred_paths:
        if path and os.path.isfile(path):
            try:
                creds = service_account.Credentials.from_service_account_file(path, scopes=SCOPES)
                logger.info(f"[Google Drive] Loaded credentials from file: {path}")
                return creds
            except Exception as e:
                logger.error(f"[Google Drive] Failed reading credentials from {path}: {e}")

    # 2. Raw JSON string from env
    raw_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if raw_json:
        try:
            info = json.loads(raw_json)
            return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        except Exception as e:
            logger.error(f"[Google Drive] Failed reading GOOGLE_SERVICE_ACCOUNT_JSON: {e}")

    # 3. Individual email and private key
    client_email = os.getenv("GOOGLE_DRIVE_CLIENT_EMAIL")
    private_key = os.getenv("GOOGLE_DRIVE_PRIVATE_KEY")
    if client_email and private_key:
        try:
            # Fix escaped newlines if passed in single-line env var
            private_key = private_key.replace("\\n", "\n")
            info = {
                "type": "service_account",
                "client_email": client_email,
                "private_key": private_key,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        except Exception as e:
            logger.error(f"[Google Drive] Failed creating credentials from email/key: {e}")

    return None

def upload_image_to_drive(
    file_bytes: bytes,
    filename: str,
    mime_type: str = "image/jpeg",
    folder_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Uploads an image to Google Drive if credentials are present.
    If Google Drive credentials are not yet configured, automatically
    saves locally in backend uploads directory as a seamless fallback.
    """
    creds = get_google_drive_credentials()
    raw_folder = folder_id or os.getenv("GOOGLE_DRIVE_FOLDER_ID") or DEFAULT_GOOGLE_DRIVE_FOLDER_ID
    target_folder_id = extract_google_drive_folder_id(raw_folder)

    if creds:
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaIoBaseUpload

            service = build("drive", "v3", credentials=creds)

            file_metadata = {
                "name": f"{uuid.uuid4().hex[:8]}_{filename}",
                "mimeType": mime_type,
            }
            if target_folder_id:
                file_metadata["parents"] = [target_folder_id]

            media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mime_type, resumable=True)

            created_file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id, name, webViewLink, webContentLink"
            ).execute()

            file_id = created_file.get("id")

            # Make publicly accessible so image displays in store & admin
            try:
                service.permissions().create(
                    fileId=file_id,
                    body={"type": "anyone", "role": "reader"},
                    fields="id"
                ).execute()
            except Exception as perm_err:
                logger.warning(f"[Google Drive] Could not set public permission: {perm_err}")

            direct_url = format_direct_google_drive_url(file_id)
            view_url = created_file.get("webViewLink") or f"https://drive.google.com/file/d/{file_id}/view"

            logger.info(f"[Google Drive] Upload success: file_id={file_id}, direct_url={direct_url}")

            return {
                "success": True,
                "file_id": file_id,
                "url": direct_url,
                "view_url": view_url,
                "provider": "google_drive",
                "filename": filename,
                "folder_id": target_folder_id,
            }

        except Exception as e:
            logger.error(f"[Google Drive] Upload failed: {e}", exc_info=True)

    # Fallback to local uploads directory
    uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    ext = os.path.splitext(filename)[1] or ".jpg"
    safe_name = f"{uuid.uuid4().hex[:12]}{ext}"
    local_path = os.path.join(uploads_dir, safe_name)

    with open(local_path, "wb") as f:
        f.write(file_bytes)

    local_url = f"/uploads/{safe_name}"
    return {
        "success": True,
        "url": local_url,
        "provider": "local_fallback",
        "filename": filename,
        "note": "Uploaded locally. To enable automatic Google Drive upload, configure Google Service Account credentials.",
    }
