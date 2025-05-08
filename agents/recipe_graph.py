from langgraph.graph import StateGraph
from langchain_core.runnables import RunnableLambda


def ask_ingredients(state):
    print("🥕 What ingredients do you have?")
    user_input = input("> ")
    state["ingredients"] = [i.strip() for i in user_input.split(",")]
    return state


def ask_preferences(state):
    print("🍽️ Any dietary restrictions? (e.g., vegan, halal, gluten-free)")
    state["preferences"]["diet"] = input("> ").strip()

    print("⚠️ Any allergies?")
    state["preferences"]["allergies"] = [a.strip() for a in input("> ").split(",")]

    print("🌍 Preferred cuisine? (e.g., Italian, Asian, Middle Eastern)")
    state["preferences"]["cuisine"] = input("> ").strip()

    print("⏱️ Maximum prep time in minutes?")
    try:
        state["preferences"]["prep_time"] = int(input("> ").strip())
    except ValueError:
        state["preferences"]["prep_time"] = 30  # fallback default

    print("😋 What are you craving today?")
    state["preferences"]["craving"] = input("> ").strip()

    return state


def final_echo(state):
    print("\n✅ Collected user preferences:")
    print(state)
    return state


def build_recipe_graph():
    builder = StateGraph(dict)

    builder.add_node("ingredients", RunnableLambda(ask_ingredients))
    builder.add_node("preferences", RunnableLambda(ask_preferences))
    builder.add_node("done", RunnableLambda(final_echo))

    builder.set_entry_point("ingredients")
    builder.add_edge("ingredients", "preferences")
    builder.add_edge("preferences", "done")

    return builder.compile()
