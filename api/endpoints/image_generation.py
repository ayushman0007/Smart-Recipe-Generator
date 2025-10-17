from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import imgGen
import os
import re
import uuid
import io
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

# Load environment variables from .env if present
load_dotenv()

router = APIRouter()

# Configure Cloudinary from environment variables at import time
CLOUD_NAME = os.getenv("CLOUD_NAME")
CLOUD_API_KEY = os.getenv("CLOUD_API_KEY")
CLOUD_API_SECRET = os.getenv("CLOUD_API_SECRET")
CLOUD_FOLDER = os.getenv("CLOUD_FOLDER", "recipes")

if CLOUD_NAME and CLOUD_API_KEY and CLOUD_API_SECRET:
    cloudinary.config(
        cloud_name=CLOUD_NAME,
        api_key=CLOUD_API_KEY,
        api_secret=CLOUD_API_SECRET,
        secure=True,
    )
else:
    # Defer raising an error until endpoint call to avoid crashing app import
    pass

class ImagePrompt(BaseModel):
    prompt: str


def _slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "image"

@router.post("/generate-image/")
async def generate_image_endpoint(payload: ImagePrompt):
    """
    Generates an image from a text prompt, uploads it to Cloudinary, and returns the image URL.
    """
    if not payload.prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    if not (CLOUD_NAME and CLOUD_API_KEY and CLOUD_API_SECRET):
        raise HTTPException(status_code=500, detail="Cloudinary environment variables are not configured.")

    try:
        # 1) Generate image bytes from prompt
        image_bytes = await imgGen.generate_image_from_prompt(payload.prompt)

        # 2) Upload to Cloudinary using a BytesIO buffer
        slug = _slugify(payload.prompt)[:60]
        unique_suffix = uuid.uuid4().hex[:8]
        public_id = f"{slug}-{unique_suffix}"

        buffer = io.BytesIO(image_bytes)
        buffer.seek(0)
        res = cloudinary.uploader.upload(
            buffer,
            folder=CLOUD_FOLDER,
            public_id=public_id,
            use_filename=True,
            unique_filename=False,
            overwrite=False,
            resource_type="image",
        )

        url = res.get("secure_url") or res.get("url")
        if not url:
            raise RuntimeError("Cloudinary upload did not return a URL.")

        return {"url": url, "public_id": res.get("public_id")}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate or upload image: {str(e)}")
