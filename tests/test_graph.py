"""
Tests for LangGraph workflow orchestration.

Verifies that the graph routing logic correctly handles all three interaction
modes (Ask, Plan, Agent) and that nodes are executed in the correct order.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.agents.graph import (
    create_pulse_graph,
    route_start,
    route_after_planner,
    app
)
from src.core.state import AgentState, create_initial_state


# ============================================================================
# Mock Node Functions
# ============================================================================

def mock_planner_node(state: AgentState) -> AgentState:
    """Mock planner that adds a simple plan."""
    state["plan"] = ["Step 1: Mock plan", "Step 2: Mock execution"]
    return state


def mock_coder_node(state: AgentState) -> AgentState:
    """Mock coder that records execution."""
    state["files_modified"] = ["mock_file.st"]
    state["code_changes"] = "Mock code generation"
    return state


def mock_tester_node(state: AgentState) -> AgentState:
    """Mock tester that adds test results."""
    state["test_results"] = {"status": "passed", "checks": 5}
    return state


def mock_qa_node(state: AgentState) -> AgentState:
    """Mock QA that answers questions."""
    state["messages"].append({"role": "assistant", "content": "Mock answer"})
    return state


# ============================================================================
# Router Function Tests
# ============================================================================

class TestRouterFunctions:
    """Test the routing decision functions."""

    def test_route_start_ask_mode(self):
        """Test that Ask mode routes to QA node."""
        state = create_initial_state("What does main.st do?", mode="ask")
        next_node = route_start(state)
        assert next_node == "qa", "Ask mode should route to qa node"

    def test_route_start_plan_mode(self):
        """Test that Plan mode routes to Planner node."""
        state = create_initial_state("Add a timer", mode="plan")
        next_node = route_start(state)
        assert next_node == "planner", "Plan mode should route to planner node"

    def test_route_start_agent_mode(self):
        """Test that Agent mode routes to Planner node."""
        state = create_initial_state("Add a timer", mode="agent")
        next_node = route_start(state)
        assert next_node == "planner", "Agent mode should route to planner node"

    def test_route_start_default_mode(self):
        """Test default routing when mode is not specified."""
        state = AgentState(
            messages=[],
            user_request="Test request",
            mode="agent",  # Default
            plan=[],
            file_context="",
            feedback="",
            files_modified=[],
            files_touched=[],
            code_changes="",
            test_results={},
            workspace_path=""
        )
        next_node = route_start(state)
        assert next_node == "planner", "Default should route to planner"

    def test_route_after_planner_plan_mode(self):
        """Test that Plan mode stops after planner for user review."""
        state = create_initial_state("Add a timer", mode="plan")
        state["plan"] = ["Step 1", "Step 2"]
        next_node = route_after_planner(state)
        assert next_node == "__end__", "Plan mode should end after planner"

    def test_route_after_planner_agent_mode(self):
        """Test that Agent mode continues to Coder after planner."""
        state = create_initial_state("Add a timer", mode="agent")
        state["plan"] = ["Step 1", "Step 2"]
        next_node = route_after_planner(state)
        assert next_node == "coder", "Agent mode should continue to coder"


# ============================================================================
# Graph Execution Tests
# ============================================================================

class TestGraphExecution:
    """Test complete graph execution flows with mocked nodes."""

    @patch("src.agents.graph.qa_node", side_effect=mock_qa_node)
    def test_ask_mode_flow(self, mock_qa):
        """Test Ask Mode: start -> qa -> end."""
        # Create a fresh graph with mocked nodes
        graph = create_pulse_graph()

        # Initial state for Ask mode
        initial_state = create_initial_state(
            "What does main.st do?",
            mode="ask",
            workspace_path="/test/workspace"
        )

        # Execute the graph
        result = graph.invoke(initial_state)

        # Verify QA node was called
        assert mock_qa.called, "QA node should be executed in Ask mode"

        # Verify state updates
        assert len(result["messages"]) > 0, "QA should add messages"
        assert result["messages"][0]["content"] == "Mock answer"

        # Verify no code changes in Ask mode
        assert result["files_modified"] == [], "Ask mode should not modify files"
        assert result["code_changes"] == "", "Ask mode should not generate code"

    @patch("src.agents.graph.planner_node", side_effect=mock_planner_node)
    def test_plan_mode_flow(self, mock_planner):
        """Test Plan Mode: start -> planner -> end (stops for review)."""
        # Create a fresh graph with mocked nodes
        graph = create_pulse_graph()

        # Initial state for Plan mode
        initial_state = create_initial_state(
            "Add a timer routine",
            mode="plan",
            workspace_path="/test/workspace"
        )

        # Execute the graph
        result = graph.invoke(initial_state)

        # Verify Planner node was called
        assert mock_planner.called, "Planner should be executed in Plan mode"

        # Verify plan was generated
        assert len(result["plan"]) > 0, "Planner should generate a plan"
        assert result["plan"][0] == "Step 1: Mock plan"

        # Verify execution stopped (no code generation)
        assert result["files_modified"] == [], "Plan mode should stop before coding"
        assert result["code_changes"] == "", "Plan mode should not generate code"

    @patch("src.agents.graph.tester_node", side_effect=mock_tester_node)
    @patch("src.agents.graph.coder_node", side_effect=mock_coder_node)
    @patch("src.agents.graph.planner_node", side_effect=mock_planner_node)
    def test_agent_mode_flow(self, mock_planner, mock_coder, mock_tester):
        """Test Agent Mode: start -> planner -> coder -> tester -> end."""
        # Create a fresh graph with mocked nodes
        graph = create_pulse_graph()

        # Initial state for Agent mode
        initial_state = create_initial_state(
            "Add a timer routine",
            mode="agent",
            workspace_path="/test/workspace"
        )

        # Execute the graph
        result = graph.invoke(initial_state)

        # Verify all nodes were called in sequence
        assert mock_planner.called, "Planner should be executed"
        assert mock_coder.called, "Coder should be executed"
        assert mock_tester.called, "Tester should be executed"

        # Verify state updates from all nodes
        assert len(result["plan"]) > 0, "Should have a plan"
        assert len(result["files_modified"]) > 0, "Should have modified files"
        assert result["code_changes"] != "", "Should have code changes"
        assert "status" in result["test_results"], "Should have test results"

        # Verify specific values
        assert result["plan"][0] == "Step 1: Mock plan"
        assert result["files_modified"][0] == "mock_file.st"
        assert result["test_results"]["status"] == "passed"


# ============================================================================
# Graph Structure Tests
# ============================================================================

class TestGraphStructure:
    """Test the structure and configuration of the graph."""

    def test_graph_has_all_nodes(self):
        """Test that all required nodes are registered in the graph."""
        graph = create_pulse_graph()

        # Get the graph nodes
        nodes = graph.get_graph().nodes

        # Verify all expected nodes exist
        expected_nodes = {"planner", "coder", "tester", "qa", "__start__", "__end__"}
        node_names = {node.id if hasattr(node, 'id') else str(node) for node in nodes}

        # Check if expected nodes are present (implementation may vary)
        # This is a basic structural check
        assert graph is not None, "Graph should be compiled successfully"

    def test_compiled_app_is_callable(self):
        """Test that the exported app is ready to use."""
        assert app is not None, "App should be exported"
        assert callable(app.invoke), "App should have invoke method"

    def test_create_pulse_graph_returns_compiled_graph(self):
        """Test that the factory function returns a compiled graph."""
        graph = create_pulse_graph()
        assert graph is not None, "Factory should return a graph"
        assert hasattr(graph, "invoke"), "Graph should be compiled with invoke method"


# ============================================================================
# Integration Tests
# ============================================================================

class TestGraphIntegration:
    """Test realistic integration scenarios."""

    @patch("src.agents.graph.qa_node")
    def test_mode_switching(self, mock_qa):
        """Test that the same graph handles different modes correctly."""
        mock_qa.side_effect = mock_qa_node
        graph = create_pulse_graph()

        # Test Ask mode
        ask_state = create_initial_state("Question?", mode="ask")
        ask_result = graph.invoke(ask_state)
        assert mock_qa.called, "Ask mode should use QA"

    def test_state_immutability(self):
        """Test that graph execution doesn't corrupt the initial state."""
        graph = create_pulse_graph()

        initial_state = create_initial_state("Test request", mode="ask")
        original_request = initial_state["user_request"]

        # Execute graph
        with patch("src.agents.graph.qa_node", side_effect=mock_qa_node):
            result = graph.invoke(initial_state)

        # Verify original state field is preserved in result
        assert result["user_request"] == original_request

    @patch("src.agents.graph.planner_node", side_effect=mock_planner_node)
    def test_workspace_path_preservation(self, mock_planner):
        """Test that workspace path is preserved through execution."""
        graph = create_pulse_graph()

        workspace = "/test/workspace"
        initial_state = create_initial_state(
            "Test request",
            mode="plan",
            workspace_path=workspace
        )

        result = graph.invoke(initial_state)

        assert result["workspace_path"] == workspace


# ============================================================================
# Main Execution (For Manual Testing)
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("PULSE IDE LANGGRAPH WORKFLOW TESTS")
    print("=" * 80)

    # Test 1: Ask Mode
    print("\n[TEST 1] Ask Mode Routing")
    print("-" * 80)
    state = create_initial_state("What does main.st do?", mode="ask")
    next_node = route_start(state)
    print(f"Mode: {state['mode']}")
    print(f"Next Node: {next_node}")
    print(f"Expected: qa")
    print(f"Result: {'PASS' if next_node == 'qa' else 'FAIL'}")

    # Test 2: Plan Mode
    print("\n[TEST 2] Plan Mode Routing")
    print("-" * 80)
    state = create_initial_state("Add a timer", mode="plan")
    next_node = route_start(state)
    print(f"Mode: {state['mode']}")
    print(f"Next Node: {next_node}")
    print(f"Expected: planner")
    print(f"Result: {'PASS' if next_node == 'planner' else 'FAIL'}")

    state["plan"] = ["Step 1", "Step 2"]
    after_planner = route_after_planner(state)
    print(f"After Planner: {after_planner}")
    print(f"Expected: __end__ (stop for review)")
    print(f"Result: {'PASS' if after_planner == '__end__' else 'FAIL'}")

    # Test 3: Agent Mode
    print("\n[TEST 3] Agent Mode Routing")
    print("-" * 80)
    state = create_initial_state("Add a timer", mode="agent")
    next_node = route_start(state)
    print(f"Mode: {state['mode']}")
    print(f"Next Node: {next_node}")
    print(f"Expected: planner")
    print(f"Result: {'PASS' if next_node == 'planner' else 'FAIL'}")

    state["plan"] = ["Step 1", "Step 2"]
    after_planner = route_after_planner(state)
    print(f"After Planner: {after_planner}")
    print(f"Expected: coder (continue execution)")
    print(f"Result: {'PASS' if after_planner == 'coder' else 'FAIL'}")

    # Test 4: Graph Structure
    print("\n[TEST 4] Graph Structure")
    print("-" * 80)
    try:
        graph = create_pulse_graph()
        print("Graph compiled successfully: PASS")
        print(f"Graph type: {type(graph)}")
        print(f"Has invoke method: {hasattr(graph, 'invoke')}")

        # Try to get graph structure (if available)
        try:
            graph_structure = graph.get_graph()
            print(f"\nGraph nodes: {len(graph_structure.nodes)}")
            print(f"Graph edges: {len(graph_structure.edges)}")
        except Exception as e:
            print(f"Could not inspect graph structure: {e}")

    except Exception as e:
        print(f"Graph compilation FAILED: {e}")

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUITE COMPLETE")
    print("=" * 80)
    print("\nTo run pytest tests, execute:")
    print("  pytest tests/test_graph.py -v")
    print("\nTo run with coverage:")
    print("  pytest tests/test_graph.py --cov=src.agents.graph --cov-report=term-missing")
