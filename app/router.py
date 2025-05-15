# router.py
from typing import Dict, Any
from state import RecipeState

def is_user_info_complete(state: Dict[str, Any]) -> str:
    recipe_state = RecipeState.model_validate(state)
    if recipe_state.ingredients:
        return "complete"
    return "incomplete"
