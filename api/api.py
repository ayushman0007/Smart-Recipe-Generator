from fastapi import APIRouter
from api.endpoints import recipes_kaggle, generative, image, image_generation

api_router = APIRouter()

# Include the router for your Kaggle recipes
api_router.include_router(recipes_kaggle.router, prefix="/recipes", tags=["Kaggle Recipes"])
api_router.include_router(generative.router, prefix="/generate", tags=["Generative AI"])
api_router.include_router(image.router, prefix="/image", tags=["Image"])
api_router.include_router(image_generation.router, prefix="/image", tags=["Image Generation"])

# You can add your other routers here as you build them
# from .endpoints import auth, recipes_external
# api_router.include_router(auth.router, ...)
# api_router.include_router(recipes_external.router, ...)