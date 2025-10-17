import logging
from typing import Dict
import re
import ast

logger = logging.getLogger(__name__)


def clean_recipe_ingredients(recipe: Dict) -> Dict:
    """
    Cleans the ingredients fields by parsing 'ingredients_raw'.
    """
    title = recipe.get('title', 'Unknown Recipe')
    logger.info(f"--- Cleaning ingredients for: {title} ---")

    raw_ingredients_str = recipe.get("ingredients_raw")

    clean_list = []

    if raw_ingredients_str and isinstance(raw_ingredients_str, str):
        try:
            # Safely parse the string representation of the list
            parsed_list = ast.literal_eval(raw_ingredients_str)

            if isinstance(parsed_list, list):
                for item in parsed_list:
                    # Further clean each ingredient item
                    clean_item = str(item).strip()
                    if clean_item:
                        clean_list.append(clean_item)
                logger.info(f"Successfully parsed and cleaned {len(clean_list)} ingredients from raw field.")
            else:
                logger.warning(f"Parsed raw ingredients data is not a list for recipe: {title}")
        except (ValueError, SyntaxError) as e:
            logger.error(f"Failed to parse 'ingredients_raw' for recipe '{title}': {e}")
    else:
        logger.info(f"No 'ingredients_raw' field found for recipe: {title}")

    # Replace the old 'ingredients_cleaned' with the newly parsed list
    recipe["ingredients_cleaned"] = clean_list

    return recipe