from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import Dict
import shutil
import os
from services import ingredienImg

router = APIRouter()

@router.post("/extract-ingredients/", response_model=Dict)
async def extract_ingredients_from_image_endpoint(file: UploadFile = File(...)):
    """
    Extracts ingredients from an uploaded image.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")

    temp_dir = "temp_images"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        ingredients = ingredienImg.extract_ingredients_from_image(file_path)

        if not ingredients:
            raise HTTPException(status_code=404, detail="Could not extract any ingredients from the image.")

        return {"ingredients": ingredients}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

