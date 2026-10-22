import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel
from app.google_drive import (
    upload_image_to_drive,
    normalize_image_url,
    extract_google_drive_id,
    format_direct_google_drive_url,
)

router = APIRouter(prefix="/upload", tags=["Upload"])

class NormalizeUrlRequest(BaseModel):
    url: str

@router.post("")
@router.post("/")
async def upload_image(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    folder_id: Optional[str] = Form(None),
):
    """
    Upload an image file directly to Google Drive or normalize a provided Google Drive link.
    Returns the direct image link (https://lh3.googleusercontent.com/d/{file_id})
    suitable for saving in the database and rendering in browser img and Next.js Image components.
    """
    if file and file.filename:
        # Read file contents
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        mime_type = file.content_type or "image/jpeg"
        result = upload_image_to_drive(
            file_bytes=content,
            filename=file.filename,
            mime_type=mime_type,
            folder_id=folder_id,
        )
        return result

    if url:
        normalized = normalize_image_url(url)
        drive_id = extract_google_drive_id(url)
        return {
            "success": True,
            "url": normalized,
            "original_url": url,
            "file_id": drive_id,
            "provider": "google_drive" if drive_id else "external",
        }

    raise HTTPException(status_code=400, detail="Either a file upload or a url must be provided.")

@router.post("/normalize")
def normalize_url(payload: NormalizeUrlRequest):
    """
    Given any Google Drive file or share link, returns the direct CDN image URL.
    """
    raw_url = payload.url.strip()
    drive_id = extract_google_drive_id(raw_url)
    normalized = normalize_image_url(raw_url)
    return {
        "original_url": raw_url,
        "normalized_url": normalized,
        "is_google_drive": bool(drive_id),
        "file_id": drive_id,
    }
