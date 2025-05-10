from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from datetime import datetime

class Preferences(BaseModel):
    """User preferences for recipe selection."""
    diet: Optional[str] = Field(
        default=None,
        description="Dietary restrictions (e.g., vegan, halal, gluten-free)"
    )
    allergies: List[str] = Field(
        default_factory=list,
        description="List of food allergies"
    )
    cuisine: Optional[str] = Field(
        default=None,
        description="Preferred cuisine type"
    )
    prep_time: Optional[str] = Field(
        default=None,
        description="Maximum preparation time in minutes"
    )
    craving: Optional[str] = Field(
        default=None,
        description="Current food craving"
    )

    @validator('prep_time')
    def validate_prep_time(cls, v):
        if v is None or v == "not specified":
            return None
        if not v.isdigit():
            raise ValueError('Prep time must be a number')
        return v

class RecipeState(BaseModel):
    """Main state for the recipe finding workflow."""
    ingredients: List[str] = Field(
        default_factory=list,
        description="Available ingredients"
    )
    preferences: Preferences = Field(
        default_factory=Preferences,
        description="User preferences for recipe selection"
    )
    recipes: List[str] = Field(
        default_factory=list,
        description="List of suggested recipes"
    )
    grocery_list: List[str] = Field(
        default_factory=list,
        description="Items needed to be purchased"
    )
    calories: Dict = Field(
        default_factory=dict,
        description="Calorie information for recipes"
    )
    steps: List[str] = Field(
        default_factory=list,
        description="Cooking steps for selected recipe"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When the state was created"
    )

    class Config:
        """Pydantic model configuration."""
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "ingredients": ["chicken", "rice"],
                "preferences": {
                    "diet": "halal",
                    "allergies": ["nuts"],
                    "cuisine": "Asian",
                    "prep_time": "30",
                    "craving": "spicy"
                }
            }
        }

# Create initial state
initial_state = RecipeState()