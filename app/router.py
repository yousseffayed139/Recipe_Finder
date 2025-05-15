# router.py
from typing import Dict, Any
from state import RecipeState
import logging

# Get logger
logger = logging.getLogger("recipe_finder")

def is_user_info_complete(state: Dict[str, Any]) -> str:
    recipe_state = RecipeState.model_validate(state)
    
    # Safely check if we have valid ingredients
    has_ingredients = bool(
        hasattr(recipe_state, 'ingredients') and 
        recipe_state.ingredients and 
        len(recipe_state.ingredients) > 0
    )
    
    if has_ingredients:
        logger.info(f"Router: found ingredients {recipe_state.ingredients}")
        return "complete"
    
    logger.info("Router: no ingredients found")
    return "incomplete"
