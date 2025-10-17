from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from services import genaitext

router = APIRouter()

class IngredientsPayload(BaseModel):
    ingredients: List[str]

@router.post("/generate-recipe/", response_model=Dict)
async def generate_recipe_endpoint(payload: IngredientsPayload):
    """
    Generate a new recipe from a list of ingredients using a generative AI model.
    """
    if not payload.ingredients:
        raise HTTPException(status_code=400, detail="Ingredients list cannot be empty.")

    recipe = genaitext.generate_recipe_with_gemini(payload.ingredients)

    if "error" in recipe:
        raise HTTPException(status_code=500, detail=f"Failed to generate recipe: {recipe['error']}")

    return recipe

