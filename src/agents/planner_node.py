"""
Planner Agent Node for Pulse IDE.

Handles "Plan Mode" and "Agent Mode" - generates a step-by-step
implementation plan from user requests. Uses CrewAI to decompose
complex tasks into actionable file modification steps.
"""

from typing import Dict, Any, List
import json

from src.core.state import AgentState
from src.core.crew_factory import CrewFactory


def planner_node(state: AgentState) -> Dict[str, Any]:
    """
    Planner Agent Node for generating implementation plans.

    This node:
    1. Extracts the user's request from state
    2. Creates a CrewAI planner crew
    3. Executes the crew to generate a structured plan
    4. Parses the result into a list of steps
    5. Returns the plan in state

    Args:
        state: Current agent state containing user_request.

    Returns:
        Dict with "plan" key containing list of implementation steps.

    Example:
        >>> state = {"user_request": "Add a motor control routine", ...}
        >>> result = planner_node(state)
        >>> print(result["plan"])
        ['Step 1: Create FUNCTION_BLOCK MotorControl in main.st', ...]

    Note:
        This node does NOT implement pause logic for Plan Mode.
        The LangGraph edge configuration will handle conditional stops.
    """
    # Extract user request
    user_request = state.get("user_request", "")

    if not user_request:
        return {
            "plan": ["Error: No user request provided"]
        }

    # Step 1: Create planner crew
    try:
        factory = CrewFactory()
        crew = factory.create_planner_crew(user_request)
    except Exception as e:
        return {
            "plan": [f"Error creating planner crew: {str(e)}"]
        }

    # Step 2: Execute the crew
    try:
        result = crew.kickoff()
    except Exception as e:
        return {
            "plan": [f"Error executing planner crew: {str(e)}"]
        }

    # Step 3: Parse the result
    # The crew is configured with output_pydantic=Plan, so result should have a .pydantic attribute
    steps_list = []

    try:
        # Try to access the Pydantic model result
        if hasattr(result, 'pydantic') and result.pydantic:
            plan_obj = result.pydantic
            if hasattr(plan_obj, 'steps'):
                steps_list = plan_obj.steps
            else:
                steps_list = [str(plan_obj)]
        # Fallback: Try to get raw output as string
        elif hasattr(result, 'raw'):
            raw_output = result.raw
            # Try to parse as JSON
            try:
                parsed = json.loads(raw_output)
                if isinstance(parsed, dict) and 'steps' in parsed:
                    steps_list = parsed['steps']
                elif isinstance(parsed, list):
                    steps_list = parsed
                else:
                    # If it's a string, try splitting by newlines
                    steps_list = [line.strip() for line in raw_output.split('\n') if line.strip()]
            except json.JSONDecodeError:
                # Fallback: Split by newlines
                steps_list = [line.strip() for line in raw_output.split('\n') if line.strip()]
        # Final fallback: Convert result to string
        else:
            result_str = str(result)
            # Try to parse as JSON first
            try:
                parsed = json.loads(result_str)
                if isinstance(parsed, dict) and 'steps' in parsed:
                    steps_list = parsed['steps']
                elif isinstance(parsed, list):
                    steps_list = parsed
                else:
                    steps_list = [result_str]
            except json.JSONDecodeError:
                # Split by newlines
                steps_list = [line.strip() for line in result_str.split('\n') if line.strip()]

    except Exception as e:
        steps_list = [f"Error parsing plan result: {str(e)}", f"Raw result: {str(result)}"]

    # Step 4: Validate and clean steps
    if not steps_list:
        steps_list = ["Error: Planner generated an empty plan"]

    # Remove any numbering prefixes (e.g., "1. ", "Step 1: ")
    cleaned_steps = []
    for step in steps_list:
        # Remove common prefixes
        step = step.strip()
        # Remove "Step N:" or "N."
        import re
        step = re.sub(r'^\d+[\.)]\s*', '', step)
        step = re.sub(r'^Step\s+\d+:\s*', '', step, flags=re.IGNORECASE)
        if step:  # Only add non-empty steps
            cleaned_steps.append(step)

    # Step 5: Return updated state
    return {
        "plan": cleaned_steps if cleaned_steps else steps_list
    }
