from app.state import RecipeState, initial_state
from app.graph import build_recipe_graph

def main():
    graph = build_recipe_graph()
    # Convert initial_state to dict for the graph
    initial_dict = initial_state.model_dump()
    result = graph.invoke(initial_dict)
    # Convert result back to RecipeState
    final_state = RecipeState.model_validate(result)
    print("\nFinal State:")
    print(final_state.model_dump_json(indent=2))

if __name__ == "__main__":
    main()
