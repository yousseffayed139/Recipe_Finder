import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file in the Recipe_Finder directory
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)

# Add the parent directory of recipe_agent to Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from app.main import main

if __name__ == "__main__":
    main() 