import os
import json
import google.generativeai as genai
from PIL import Image
from typing import List

# It's best practice to load your key from your .env file
# from dotenv import load_dotenv
# load_dotenv()
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# For demonstration, we'll use the hardcoded key from your previous prompts
GEMINI_API_KEY = "AIzaSyByzQrx5FP9QdSBYz5waqf1tf91KqvNvJQ"

try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Error configuring Gemini API: {e}")


def extract_ingredients_from_image(image_path: str) -> List[str]:
    """
    Extracts a list of ingredients from an image using a Gemini multimodal model.

    Args:
        image_path: The local file path to the image.

    Returns:
        A list of identified ingredient strings, or an empty list if an error occurs.
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        image = Image.open(image_path)
    except Exception as e:
        print(f"Failed to initialize model or open image: {e}")
        return []

    # The multimodal prompt containing both the text instruction and the image
    prompt = [
        """
        Analyze the provided image of groceries. Identify only the edible food items
        and ingredients. Ignore any non-food items like bowls, countertops, or packaging text.

        Return your response as a single, valid JSON object with a single key "ingredients",
        which is an array of strings. For example: {"ingredients": ["tomato", "onion", "garlic"]}.

        Do not include any other text or explanation.
        """,
        image
    ]

    print(f"Sending image '{image_path}' to Gemini for ingredient extraction...")

    try:
        response = model.generate_content(prompt)

        # Clean the response to ensure it's a valid JSON string
        cleaned_response = response.text.strip().lstrip("```json").rstrip("```")

        # Parse the JSON and extract the list
        data = json.loads(cleaned_response)
        return data.get("ingredients", [])

    except Exception as e:
        print(f"An error occurred during ingredient extraction: {e}")
        return []


# --- Example Usage (you can run this file directly to test) ---
if __name__ == "__main__":
    # Create a dummy image file for testing named 'test_image.jpg'
    # Or replace this path with a real image of groceries on your computer
    test_image_path = "img.png"

    if os.path.exists(test_image_path):
        ingredients = extract_ingredients_from_image(test_image_path)
        if ingredients:
            print("\n--- Detected Ingredients ---")
            for ingredient in ingredients:
                print(f"- {ingredient}")
        else:
            print("\nCould not detect any ingredients.")
    else:
        print(f"Test image not found at '{test_image_path}'. Please create it or update the path.")
