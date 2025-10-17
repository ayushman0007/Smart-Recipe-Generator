from fastapi import APIRouter, HTTPException, Query
from typing import List

# Correctly import from sibling/parent packages within the 'app' module
from crud import crud_recipe
from schemas.recipe import Recipe
from utils.formatters import clean_recipe_ingredients

router = APIRouter()

@router.get("/", response_model=List[Recipe])
async def read_recipes(skip: int = 0, limit: int = 20):
    """
    Retrieve a paginated list of recipes.
    Ingredients are cleaned on-the-fly for each recipe.
    """
    # 1. Fetch the raw data
    recipes_from_db = await crud_recipe.get_recipes(skip=skip, limit=limit)

    # 2. Apply the cleaning function to each recipe
    cleaned_recipes = [clean_recipe_ingredients(recipe) for recipe in recipes_from_db]

    # 3. Return the cleaned recipes
    return cleaned_recipes

@router.get("/{recipe_id}", response_model=Recipe)
async def read_recipe(recipe_id: str):
    """
    Retrieve a single recipe by its ID.
    Ingredients are cleaned on-the-fly before returning.
    """
    recipe_from_db = await crud_recipe.get_recipe_by_id(recipe_id)
    if recipe_from_db is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Apply the cleaning function and return the result
    cleaned_recipe = clean_recipe_ingredients(recipe_from_db)
    return cleaned_recipe

@router.get("/by-ingredients/", response_model=List[Recipe])
async def search_recipes_by_ingredients(
    ingredients: List[str] = Query(
        ...,
        title="Search Ingredients",
        description="Provide one or more ingredients to find matching recipes."
    )
):
    """
    Search for recipes that contain all of the provided ingredients.
    """
    # 1. Fetch the matching recipes using the new CRUD function
    recipes_from_db = await crud_recipe.find_recipes_by_ingredients(ingredients=ingredients)

    if not recipes_from_db:
        # It's better to return an empty list than a 404 for a search
        return []

    # 2. Apply the on-the-fly cleaning formatter to ensure consistent output
    cleaned_recipes = [clean_recipe_ingredients(recipe) for recipe in recipes_from_db]

    # 3. Return the cleaned, matching recipes
    return cleaned_recipes