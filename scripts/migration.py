import asyncio
import logging
import ast
import sys
import os

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.mongodb import db
from utils.formatters import clean_recipe_ingredients

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TARGET_COLLECTION = "recipes"

async def clean_data_in_place():
    """
    Reads data from the target collection, cleans it, and updates it in-place.
    """
    collection = db[TARGET_COLLECTION]
    total_documents = await collection.count_documents({})
    logging.info(f"Found {total_documents} documents to process in '{TARGET_COLLECTION}'.")

    processed_count = 0
    async for recipe in collection.find():
        try:
            recipe_id = recipe["_id"]
            ingredients_raw = recipe.get("Ingredients")

            if isinstance(ingredients_raw, str):
                try:
                    # The data is a string representation of a list
                    ingredients_list = ast.literal_eval(ingredients_raw)
                except (ValueError, SyntaxError) as e:
                    logging.error(f"Could not parse ingredients for recipe {recipe_id}: {e}")
                    continue
            elif isinstance(ingredients_raw, list):
                ingredients_list = ingredients_raw
            else:
                logging.warning(f"Skipping recipe {recipe_id} due to unexpected type for Ingredients: {type(ingredients_raw)}")
                continue

            cleaned_ingredients = clean_recipe_ingredients(ingredients_list)

            await collection.update_one(
                {"_id": recipe_id},
                {"$set": {"CleanedIngredients": cleaned_ingredients}}
            )
            processed_count += 1
            if processed_count % 100 == 0 or processed_count == total_documents:
                logging.info(f"Processed {processed_count}/{total_documents} recipes.")

        except Exception as e:
            logging.error(f"Failed to process recipe {recipe.get('_id')}: {e}")

    logging.info(f"Finished processing. Total recipes updated: {processed_count}")


if __name__ == "__main__":
    asyncio.run(clean_data_in_place())
