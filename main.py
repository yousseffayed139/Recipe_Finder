from state import initial_state
from agents.recipe_graph import build_recipe_graph

def main():
    graph = build_recipe_graph()
    final_state = graph.invoke(initial_state)
    print(final_state)

if __name__ == "__main__":
    main()
