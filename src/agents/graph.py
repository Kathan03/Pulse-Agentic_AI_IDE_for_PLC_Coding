"""
LangGraph Workflow Orchestration for Pulse IDE.

Defines the multi-agent workflow that routes between nodes based on the
selected interaction mode (Ask, Plan, Agent). This is the core orchestration
layer that manages state flow through the agent system.

Graph Structure:
    Ask Mode:    start -> qa -> end
    Plan Mode:   start -> planner -> end (user reviews plan)
    Agent Mode:  start -> planner -> coder -> tester -> end
"""

from langgraph.graph import StateGraph, END
from src.core.state import AgentState
from src.agents import planner_node, coder_node, tester_node, qa_node


# ============================================================================
# Router Functions
# ============================================================================

def route_start(state: AgentState) -> str:
    """
    Route from the entry point based on the selected mode.

    This conditional entry point determines the first node to execute
    based on the user's selected interaction mode.

    Args:
        state: Current agent state containing the mode field.

    Returns:
        str: Name of the next node to execute.
            - "qa" if mode is "ask" (Q&A only, no code changes)
            - "planner" if mode is "plan" or "agent" (generate implementation plan)

    Example:
        >>> state = {"mode": "ask", ...}
        >>> route_start(state)
        'qa'
    """
    mode = state.get("mode", "agent")

    if mode == "ask":
        # Ask Mode: Go directly to Q&A, skip planning/coding
        return "qa"

    # Plan Mode or Agent Mode: Start with planning
    return "planner"


def route_after_planner(state: AgentState) -> str:
    """
    Route after the Planner node based on the mode.

    Determines whether to stop for user review (Plan Mode) or continue
    to code execution (Agent Mode).

    Args:
        state: Current agent state containing the mode field.

    Returns:
        str: Name of the next node or END.
            - END if mode is "plan" (stop for user approval)
            - "coder" if mode is "agent" (continue to execution)

    Example:
        >>> state = {"mode": "plan", ...}
        >>> route_after_planner(state)
        '__end__'
    """
    mode = state.get("mode", "agent")

    if mode == "plan":
        # Plan Mode: Stop here so user can review and approve the plan
        return END

    # Agent Mode: Continue to code generation
    return "coder"


# ============================================================================
# Graph Construction
# ============================================================================

def create_pulse_graph() -> StateGraph:
    """
    Create and compile the Pulse IDE agent workflow graph.

    Constructs a LangGraph StateGraph with the following structure:

    Nodes:
        - planner: Generates implementation plans
        - coder: Writes code to disk
        - tester: Validates generated code
        - qa: Answers questions via RAG

    Edges:
        - Conditional entry based on mode (route_start)
        - Conditional exit from planner (route_after_planner)
        - Linear flow: coder -> tester -> end
        - Direct flow: qa -> end

    Returns:
        StateGraph: Compiled LangGraph workflow ready for execution.

    Example:
        >>> graph = create_pulse_graph()
        >>> result = graph.invoke({"mode": "agent", "user_request": "Add timer"})
    """
    # Initialize the workflow with AgentState schema
    workflow = StateGraph(AgentState)

    # ========================================================================
    # Add Nodes
    # ========================================================================
    workflow.add_node("planner", planner_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("tester", tester_node)
    workflow.add_node("qa", qa_node)

    # ========================================================================
    # Add Edges
    # ========================================================================

    # Entry Point: Route based on mode
    workflow.set_conditional_entry_point(route_start)

    # Planner Exit: Stop for review (Plan) or continue (Agent)
    workflow.add_conditional_edges("planner", route_after_planner)

    # Standard Flow: Coder -> Tester -> End
    workflow.add_edge("coder", "tester")
    workflow.add_edge("tester", END)

    # QA Flow: Direct to end
    workflow.add_edge("qa", END)

    # ========================================================================
    # Compile the Graph
    # ========================================================================
    return workflow.compile()


# ============================================================================
# Export Compiled Graph
# ============================================================================

# Create the compiled graph instance for use by the UI
app = create_pulse_graph()

# Export both the compiled graph and the factory function
__all__ = ["app", "create_pulse_graph", "route_start", "route_after_planner"]
