import os
from dotenv import load_dotenv
from smolagents import ToolCallingAgent, InferenceClientModel, tool
from typing import Dict, Any
import json
import random

load_dotenv()

# Use a free Hugging Face Inference API model.
# Token is read automatically from env var HUGGINGFACEHUB_API_TOKEN.
model = InferenceClientModel(model_id=os.getenv("HF_MODEL_ID", "HuggingFaceH4/zephyr-7b-beta"))

# Global state for simplicity
DISTRIBUTION_HISTORY = {}

@tool
def check_history(penguin_name: str) -> Dict[str, Any]:
    """Check the recent resource distribution history for a specific penguin."""
    history = DISTRIBUTION_HISTORY.get(penguin_name, [])
    recent_food = sum(h["food"] for h in history[-3:]) if history else 0
    has_tool = any(h["has_tool"] for h in history) if history else False
    return {"recent_food": recent_food, "has_tool": has_tool}

@tool
def record_distribution(penguin_name: str, food: int, has_tool: bool) -> str:
    """Record the distribution of resources."""
    if penguin_name not in DISTRIBUTION_HISTORY:
        DISTRIBUTION_HISTORY[penguin_name] = []
    DISTRIBUTION_HISTORY[penguin_name].append({"food": food, "has_tool": has_tool})
    return f"Recorded: {penguin_name} got {food} got {food} food and {'a' if has_tool else 'no'} tool"

@tool
def find_food(penguin_name: str, method: str) -> int:
    """Return a small random food yield based on the method used.

    Args:
        penguin_name: The name of the penguin finding food.
        method: The method used to find food. 'fishing' yields 2-7, otherwise 0-3.
    """
    if method == "fishing":
        amount = random.randint(2, 7)
    else:
        amount = random.randint(0, 3)
    print(f"🐟 {penguin_name} went {method} and found {amount} food!")
    return amount

class ScientistAgent(ToolCallingAgent):
    def __init__(self, initial_food_supply: int = 20, refresh_interval: int = 5) -> None:
        super().__init__(
            tools=[check_history, record_distribution],
            model=model,
            name="scientist",
            description="A scientist responding to penguin actions",
        )
        self.initial_food_supply = initial_food_supply
        self.food_supply = initial_food_supply
        self.tool_available = True
        self.refresh_interval = refresh_interval
        self.turn_counter = 0

    def refresh_resources(self):
        """Periodically refresh the scientist's food supply."""
        self.food_supply = self.initial_food_supply
        self.tool_available = True
        print("\n🔄 Scientist Resources Refreshed!")
        print(f"Food Supply Reset to: {self.food_supply}")
        print(f"Tool Availability Reset to: {self.tool_available}")

    def respond_to_action(self, penguin: 'PenguinAgent', penguin_action: Dict[str, Any]) -> None:
        """Respond to a penguin's action."""
        self.turn_counter += 1
        if self.turn_counter % self.refresh_interval == 0:
            self.refresh_resources()

        print(f"\n--- Turn {self.turn_counter}: Scientist Responds to {penguin.name} ---")
        print(f"Penguin Action: {penguin_action}")
        print("Penguin State:")
        print(f"  - Food: {penguin.food}")
        print(f"  - Has Tool: {penguin.has_tool}")

        history = check_history(penguin.name)
        print("Penguin History:")
        print(f"  - Recent Food: {history['recent_food']}")
        print(f"  - Has Had Tool: {history['has_tool']}")

        print("\nScientist Resources:")
        print(f"  - Food Supply: {self.food_supply}")
        print(f"  - Tool Available: {self.tool_available}")

        response = self.run(
            f"""Penguin {penguin.name} took action: {penguin_action}
            Penguin's current state:
            - Food: {penguin.food}
            - Has Tool: {penguin.has_tool}

            Recent History: {history['recent_food']} recent food, {'has' if history['has_tool'] else 'no'} tool.
            Available Scientist Resources: {self.food_supply} food, Tool: {self.tool_available}

            Respond with JSON: {{"give_food": <0-5>, "give_tool": <bool>}}"""
        )

        try:
            decision = response if isinstance(response, dict) else json.loads(str(response).split("final_answer:")[-1].strip())
            food = min(int(decision.get('give_food', 0)), self.food_supply)
            tool = bool(decision.get('give_tool', False)) and self.tool_available

            print("\nScientist's Decision:")
            print(f"  - Food to Give: {food}")
            print(f"  - Tool to Give: {tool}")

            if food > 0:
                self.food_supply -= food
                penguin.food += food
            if tool:
                penguin.has_tool = True
                self.tool_available = False

            record_distribution(penguin.name, food, tool)

            print("\nPost-Action State:")
            print("Scientist Resources:")
            print(f"  - Remaining Food Supply: {self.food_supply}")
            print(f"  - Tool Available: {self.tool_available}")
            print(f"Penguin {penguin.name}:")
            print(f"  - Food: {penguin.food}")
            print(f"  - Has Tool: {penguin.has_tool}")
        except Exception as e:
            print(f"Error processing scientist's response: {e}")

class PenguinAgent(ToolCallingAgent):
    def __init__(self, name: str) -> None:
        super().__init__(tools=[find_food], model=model, name=name)
        self.name = name
        self.food = 0
        self.has_tool = False

    def take_action(self) -> Dict[str, Any]:
        """Penguin decides on an action each round."""
        _ = check_history(self.name)  # context if you want to use it in your prompt

        prompt = f"""You are Penguin {self.name}.
        You have {self.food} food.
        You have {'a' if self.has_tool else 'no'} tool.
        If you have a tool, you should prefer to 'find_food' with method 'fishing'.
        If you do not have a tool, you can 'find_food' with method 'foraging' or 'request_food'.
        What do you want to do? Respond with JSON:  {{'action': '<action_string>', 'method': '<method_string>'}}"""

        response = self.run(prompt)

        try:
            return response if isinstance(response, dict) else json.loads(str(response).split("final_answer:")[-1].strip())
        except Exception:
            print(f"Error processing {self.name}'s action; falling back to safe action.")
            return {"action": "request_food", "details": "default safe action"}

def run_simulation():
    scientist = ScientistAgent(initial_food_supply=20, refresh_interval=5)
    penguins = [PenguinAgent(f"Penguin {i}") for i in range(4)]

    print("\nStarting Simulation...")
    for round_idx in range(3):
        print(f"\n{'='*50}")
        print(f"ROUND {round_idx + 1}")
        print(f"{'='*50}")

        # Penguins take actions
        penguin_actions = {}
        for penguin in penguins:
            action = penguin.take_action()
            penguin_actions[penguin.name] = action
            print(f"{penguin.name} Action: {action}")

        # Process Penguin Actions
        for penguin in penguins:
            act = penguin_actions[penguin.name].get("action")
            if act == "request_food":
                pass  # handled by scientist
            elif act == "find_food":
                # This will work after you implement and register find_food
                method = penguin_actions[penguin.name].get("method", "foraging")
                # Ensure method is valid if LLM hallucinates
                if method not in ["fishing", "foraging"]:
                    method = "foraging"
                food_found = find_food(penguin.name, method)
                penguin.food += food_found

        # Scientist responds to actions
        for penguin in penguins:
            scientist.respond_to_action(penguin, penguin_actions[penguin.name])

    print("\nFinal State:")
    print(f"Remaining: {scientist.food_supply} food, {'🔨' if scientist.tool_available else ''}")
    for penguin in penguins:
        hist = check_history(penguin.name)
        print(f"{penguin.name} - Total Food: {penguin.food}, Has Tool: {hist['has_tool']}")

if __name__ == "__main__":
    run_simulation()
