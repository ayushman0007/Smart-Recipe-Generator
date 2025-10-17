# stir-backend/app/schemas/recipe.py

from pydantic import BaseModel
from typing import List, Optional
from .common import MongoBaseModel

class ImageMeta(BaseModel):
    url: str
    public_id: str
    width: int
    height: int
    format: str

class Recipe(MongoBaseModel):
    title: str
    ingredients_cleaned: List[str]
    instructions: str
    image: Optional[ImageMeta] = None

    class Config:
        from_attributes = True