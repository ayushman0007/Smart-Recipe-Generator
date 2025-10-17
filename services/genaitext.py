import os
import json
import google.generativeai as genai
from typing import List, Dict, Optional
from PIL import Image
from io import BytesIO

# --- WARNING: Do not hardcode your API key in production code ---
# It is strongly recommended to use environment variables.
# For example: GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_KEY = "AIzaSyByzQrx5FP9QdSBYz5waqf1tf91KqvNvJQ"

# --- Configure the Gemini API client ---
try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Error configuring Gemini API: {e}")


def generate_recipe_with_gemini(ingredients: List[str]) -> Dict:
    """
    Generates a recipe using the Gemini API based on a list of ingredients.
    """
    try:
        text_model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        return {"error": f"Could not initialize text model: {e}"}

    ingredient_string = ", ".join(ingredients)
    prompt = f"""
    You are a creative and experienced chef. Your task is to create a delicious recipe
    using the following ingredients: {ingredient_string}.

    Please respond with ONLY a single, valid JSON object. Do not include any text,
    explanation, or markdown formatting before or after the JSON object.

    The JSON object must have the following structure:
    {{
      "title": "A creative and fitting title for the recipe",
      "description": "A brief, appealing one-sentence description of the dish.",
      "servings": "e.g., 2-4 people",
      "prep_time": "e.g., 15 minutes",
      "cook_time": "e.g., 30 minutes",
      "ingredients": [
        {{ "item": "Full ingredient name", "quantity": "e.g., 2 cups or 100g" }}
      ],
      "instructions": [
        "Step-by-step instruction 1.",
        "Step-by-step instruction 2.",
        "..."
      ]
    }}
    """

    try:
        print("Generating recipe with Gemini...")
        response = text_model.generate_content(prompt)
        cleaned_response = response.text.strip().lstrip("```json").rstrip("```")
        recipe_data = json.loads(cleaned_response)
        return recipe_data
    except Exception as e:
        print(f"An error occurred during recipe generation: {e}")
        return {"error": str(e)}


def generate_image_with_gemini(recipe_title: str, recipe_description: str) -> Optional[bytes]:
    """
    Generates a recipe image using a Gemini image generation model.

    Args:
        recipe_title: The title of the recipe.
        recipe_description: A short description of the recipe.

    Returns:
        The raw bytes of the generated PNG image, or None if generation fails.
    """
    try:
        # NOTE: The model name for image generation can change.
        # Use a model specifically designed for this, like 'gemini-1.5-flash' or a future equivalent.
        image_model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"Could not initialize image model: {e}")
        return None

    # Create a detailed prompt for the image generation model
    image_prompt = (
        f"Generate a vibrant, professional food photography image of '{recipe_title}'. "
        f"{recipe_description}. The dish should look delicious and be presented in a "
        "fancy restaurant style. The overall theme should be futuristic and sleek, "
        "inspired by Gemini. High resolution, photorealistic."
    )

    print(f"\nSending prompt to Gemini for image generation: '{image_prompt}'")

    try:
        # Generate the image content
        response = image_model.generate_content(image_prompt)

        # Extract the image data from the response parts
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                print("Image data received successfully.")
                return part.inline_data.data  # Return the raw image bytes

        print("Image generation finished, but no image data was found in the response.")
        return None

    except Exception as e:
        print(f"An error occurred during image generation: {e}")
        return None


# --- Example Usage ---
if __name__ == "__main__":
    my_ingredients = ["wild salmon fillet", "asparagus spears", "lemon", "dill", "quinoa"]
    print(f"My ingredients: {', '.join(my_ingredients)}\n")

    # 1. Generate the recipe
    generated_recipe = generate_recipe_with_gemini(my_ingredients)

    if "error" not in generated_recipe:
        print("\n--- Generated Recipe ---")
        print(json.dumps(generated_recipe, indent=2))

        # 2. Generate an image for the recipe
        recipe_title = generated_recipe.get("title", "Untitled Recipe")
        recipe_desc = generated_recipe.get("description", "A delicious dish")

        image_bytes = generate_image_with_gemini(recipe_title, recipe_desc)

        # 3. Save the generated image to a file
        if image_bytes:
            try:
                image = Image.open(BytesIO(image_bytes))
                file_name = "generated_recipe_image.png"
                image.save(file_name)
                print(f"\n--- Image Saved ---")
                print(f"Successfully saved image to '{file_name}'")
            except Exception as e:
                print(f"Failed to save image: {e}")
        else:
            print("\nCould not generate an image for the recipe.")
    else:
        print("\nCould not generate recipe.")