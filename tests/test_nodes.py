"""
Test Suite for LangGraph Agent Nodes.

Tests the QA and Planner nodes to verify:
1. QA Node correctly retrieves context and generates answers
2. Planner Node generates valid implementation plans
3. State updates are handled correctly
4. Error handling works as expected

Run with: pytest tests/test_nodes.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import AIMessage

from src.agents.qa_node import qa_node
from src.agents.planner_node import planner_node
from src.core.state import AgentState, create_initial_state
from src.core.crew_factory import Plan


class TestQANode:
    """Test cases for QA Agent Node functionality."""

    def test_qa_node_with_empty_request(self):
        """Test QA node handles empty user request gracefully."""
        state = create_initial_state(user_request="", mode="ask")

        result = qa_node(state)

        assert "messages" in result
        assert len(result["messages"]) > 0
        assert isinstance(result["messages"][0], AIMessage)
        assert "no question" in result["messages"][0].content.lower()
        print("\n[OK] QA node handles empty request correctly")

    @patch('src.agents.qa_node.get_rag')
    @patch('src.agents.qa_node.ChatOpenAI')
    def test_qa_node_with_rag_results(self, mock_llm_class, mock_get_rag):
        """Test QA node with successful RAG retrieval and LLM response."""
        # Mock RAG search results
        mock_rag = Mock()
        mock_rag.search_codebase.return_value = [
            {
                "content": "FUNCTION_BLOCK MotorControl\nVAR\n  bRunning: BOOL;\nEND_VAR\nEND_FUNCTION_BLOCK",
                "metadata": {"path": "main.st", "chunk_index": 0}
            },
            {
                "content": "VAR GLOBAL\n  gMotor: MotorControl;\nEND_VAR",
                "metadata": {"path": "globals.st", "chunk_index": 0}
            }
        ]
        mock_get_rag.return_value = mock_rag

        # Mock LLM response
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "The MotorControl function block manages motor state with a bRunning boolean variable (main.st:1)."
        mock_llm.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm

        # Create state and call node
        state = create_initial_state(
            user_request="What does the MotorControl function block do?",
            mode="ask"
        )

        result = qa_node(state)

        # Verify RAG was called
        mock_rag.search_codebase.assert_called_once_with(
            query="What does the MotorControl function block do?",
            n_results=5
        )

        # Verify LLM was called
        assert mock_llm.invoke.called

        # Verify result structure
        assert "messages" in result
        assert len(result["messages"]) > 0
        assert isinstance(result["messages"][0], AIMessage)
        assert "MotorControl" in result["messages"][0].content
        assert "file_context" in result

        print("\n[OK] QA node processes RAG results and generates answer")

    @patch('src.agents.qa_node.get_rag')
    @patch('src.agents.qa_node.ChatOpenAI')
    def test_qa_node_with_no_rag_results(self, mock_llm_class, mock_get_rag):
        """Test QA node when RAG returns no results."""
        # Mock RAG with empty results
        mock_rag = Mock()
        mock_rag.search_codebase.return_value = []
        mock_get_rag.return_value = mock_rag

        # Mock LLM response
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "No relevant code found in the codebase to answer this question."
        mock_llm.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm

        state = create_initial_state(
            user_request="What is the airspeed velocity of an unladen swallow?",
            mode="ask"
        )

        result = qa_node(state)

        # Verify result
        assert "messages" in result
        assert len(result["messages"]) > 0
        assert "file_context" in result
        assert "No relevant code found" in result["file_context"]

        print("\n[OK] QA node handles empty RAG results gracefully")

    @patch('src.agents.qa_node.get_rag')
    @patch('src.agents.qa_node.ChatOpenAI')
    def test_qa_node_with_llm_error(self, mock_llm_class, mock_get_rag):
        """Test QA node handles LLM errors gracefully."""
        # Mock RAG
        mock_rag = Mock()
        mock_rag.search_codebase.return_value = [
            {"content": "test content", "metadata": {"path": "test.st"}}
        ]
        mock_get_rag.return_value = mock_rag

        # Mock LLM to raise exception
        mock_llm = Mock()
        mock_llm.invoke.side_effect = Exception("API rate limit exceeded")
        mock_llm_class.return_value = mock_llm

        state = create_initial_state(user_request="Test question", mode="ask")

        result = qa_node(state)

        # Verify error is handled
        assert "messages" in result
        assert "Error generating answer" in result["messages"][0].content

        print("\n[OK] QA node handles LLM errors gracefully")


class TestPlannerNode:
    """Test cases for Planner Agent Node functionality."""

    def test_planner_node_with_empty_request(self):
        """Test Planner node handles empty user request gracefully."""
        state = create_initial_state(user_request="", mode="plan")

        result = planner_node(state)

        assert "plan" in result
        assert len(result["plan"]) > 0
        assert "error" in result["plan"][0].lower()
        print("\n[OK] Planner node handles empty request correctly")

    @patch('src.agents.planner_node.CrewFactory')
    def test_planner_node_with_valid_plan(self, mock_factory_class):
        """Test Planner node with successful crew execution."""
        # Mock the crew result
        mock_plan = Plan(steps=[
            "Create FUNCTION_BLOCK MotorControl in main.st",
            "Add VAR section with bRunning: BOOL variable",
            "Implement start/stop logic in function block body",
            "Declare global instance in globals.st"
        ])

        mock_result = Mock()
        mock_result.pydantic = mock_plan

        mock_crew = Mock()
        mock_crew.kickoff.return_value = mock_result

        mock_factory = Mock()
        mock_factory.create_planner_crew.return_value = mock_crew
        mock_factory_class.return_value = mock_factory

        # Create state and call node
        state = create_initial_state(
            user_request="Add a motor control routine with start/stop logic",
            mode="plan"
        )

        result = planner_node(state)

        # Verify factory and crew were called
        mock_factory.create_planner_crew.assert_called_once_with(
            "Add a motor control routine with start/stop logic"
        )
        mock_crew.kickoff.assert_called_once()

        # Verify result structure
        assert "plan" in result
        assert len(result["plan"]) == 4
        assert "MotorControl" in result["plan"][0]
        assert all(isinstance(step, str) for step in result["plan"])

        print("\n[OK] Planner node generates valid plan")

    @patch('src.agents.planner_node.CrewFactory')
    def test_planner_node_cleans_step_numbering(self, mock_factory_class):
        """Test that Planner node removes step numbering prefixes."""
        # Mock crew result with numbered steps
        mock_plan = Plan(steps=[
            "1. Create FUNCTION_BLOCK MotorControl",
            "2. Add VAR section",
            "Step 3: Implement logic",
            "4) Add documentation"
        ])

        mock_result = Mock()
        mock_result.pydantic = mock_plan

        mock_crew = Mock()
        mock_crew.kickoff.return_value = mock_result

        mock_factory = Mock()
        mock_factory.create_planner_crew.return_value = mock_crew
        mock_factory_class.return_value = mock_factory

        state = create_initial_state(
            user_request="Add motor control",
            mode="plan"
        )

        result = planner_node(state)

        # Verify numbering is removed
        assert "plan" in result
        assert result["plan"][0] == "Create FUNCTION_BLOCK MotorControl"
        assert result["plan"][1] == "Add VAR section"
        assert result["plan"][2] == "Implement logic"
        assert result["plan"][3] == "Add documentation"

        print("\n[OK] Planner node cleans step numbering")

    @patch('src.agents.planner_node.CrewFactory')
    def test_planner_node_with_string_fallback(self, mock_factory_class):
        """Test Planner node handles non-Pydantic result format."""
        # Mock crew result without pydantic attribute (fallback to raw)
        mock_result = Mock()
        mock_result.pydantic = None
        mock_result.raw = """Step 1: Create file
Step 2: Add code
Step 3: Test"""

        mock_crew = Mock()
        mock_crew.kickoff.return_value = mock_result

        mock_factory = Mock()
        mock_factory.create_planner_crew.return_value = mock_crew
        mock_factory_class.return_value = mock_factory

        state = create_initial_state(user_request="Test request", mode="plan")

        result = planner_node(state)

        # Verify fallback parsing works
        assert "plan" in result
        assert len(result["plan"]) == 3
        assert "Create file" in result["plan"][0]

        print("\n[OK] Planner node handles string fallback")

    @patch('src.agents.planner_node.CrewFactory')
    def test_planner_node_with_json_fallback(self, mock_factory_class):
        """Test Planner node handles JSON string result."""
        # Mock crew result with JSON string
        mock_result = Mock()
        mock_result.pydantic = None
        mock_result.raw = '{"steps": ["Step A", "Step B", "Step C"]}'

        mock_crew = Mock()
        mock_crew.kickoff.return_value = mock_result

        mock_factory = Mock()
        mock_factory.create_planner_crew.return_value = mock_crew
        mock_factory_class.return_value = mock_factory

        state = create_initial_state(user_request="Test request", mode="plan")

        result = planner_node(state)

        # Verify JSON parsing works
        assert "plan" in result
        assert len(result["plan"]) == 3
        assert result["plan"][0] == "Step A"
        assert result["plan"][1] == "Step B"

        print("\n[OK] Planner node parses JSON fallback")

    @patch('src.agents.planner_node.CrewFactory')
    def test_planner_node_with_crew_error(self, mock_factory_class):
        """Test Planner node handles crew execution errors."""
        # Mock crew to raise exception
        mock_crew = Mock()
        mock_crew.kickoff.side_effect = Exception("Crew execution failed")

        mock_factory = Mock()
        mock_factory.create_planner_crew.return_value = mock_crew
        mock_factory_class.return_value = mock_factory

        state = create_initial_state(user_request="Test request", mode="plan")

        result = planner_node(state)

        # Verify error is handled
        assert "plan" in result
        assert "Error executing planner crew" in result["plan"][0]

        print("\n[OK] Planner node handles crew errors gracefully")

    @patch('src.agents.planner_node.CrewFactory')
    def test_planner_node_with_factory_error(self, mock_factory_class):
        """Test Planner node handles factory creation errors."""
        # Mock factory to raise exception
        mock_factory_class.side_effect = Exception("API key not configured")

        state = create_initial_state(user_request="Test request", mode="plan")

        result = planner_node(state)

        # Verify error is handled
        assert "plan" in result
        assert "Error creating planner crew" in result["plan"][0]

        print("\n[OK] Planner node handles factory errors gracefully")


class TestStateManagement:
    """Test cases for state creation and management."""

    def test_create_initial_state(self):
        """Test initial state creation with default values."""
        state = create_initial_state(
            user_request="Test request",
            mode="agent",
            workspace_path="/path/to/workspace"
        )

        assert state["user_request"] == "Test request"
        assert state["mode"] == "agent"
        assert state["workspace_path"] == "/path/to/workspace"
        assert state["messages"] == []
        assert state["plan"] == []
        assert state["files_modified"] == []
        assert isinstance(state["test_results"], dict)

        print("\n[OK] Initial state created correctly")

    def test_state_mode_types(self):
        """Test that all valid mode types work."""
        for mode in ["ask", "plan", "agent"]:
            state = create_initial_state(user_request="Test", mode=mode)
            assert state["mode"] == mode

        print("\n[OK] All mode types work correctly")


# ============================================================================
# Integration Tests (require actual API calls)
# ============================================================================

class TestNodesIntegration:
    """Integration tests that make real API calls."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup fixture to skip tests if API key not configured."""
        from src.core.config import Config
        if not Config.OPENAI_API_KEY:
            pytest.skip("OPENAI_API_KEY not configured. Add it to .env to run integration tests.")

    @pytest.mark.integration
    def test_planner_node_integration(self):
        """
        Integration test: Run planner node with real API call.

        WARNING: This test incurs OpenAI API costs.
        """
        print("\n" + "="*60)
        print("INTEGRATION TEST: Planner Node")
        print("="*60)

        state = create_initial_state(
            user_request="Add a motor control routine with emergency stop",
            mode="plan"
        )

        print(f"\nUser Request: {state['user_request']}")
        print("\nExecuting planner node (this may take 10-30 seconds)...")

        result = planner_node(state)

        # Verify result
        assert "plan" in result
        assert len(result["plan"]) > 0
        assert not any("error" in step.lower() for step in result["plan"])

        print(f"\n[PLAN] Generated Plan ({len(result['plan'])} steps):")
        print("-" * 60)
        for i, step in enumerate(result["plan"], 1):
            print(f"{i}. {step}")
        print("-" * 60)

        print("\n[OK] Planner node integration test passed")


# ============================================================================
# Manual Test Runner
# ============================================================================

def run_manual_tests():
    """
    Run manual tests without pytest for quick verification.

    Usage: python tests/test_nodes.py
    """
    print("="*70)
    print("MANUAL NODE TESTS")
    print("="*70)

    try:
        # Test 1: QA Node with mocks
        print("\n[1/2] Testing QA Node (mocked)...")
        print("-" * 70)

        with patch('src.agents.qa_node.get_rag') as mock_get_rag, \
             patch('src.agents.qa_node.ChatOpenAI') as mock_llm:

            mock_rag = Mock()
            mock_rag.search_codebase.return_value = [
                {"content": "test code", "metadata": {"path": "test.st"}}
            ]
            mock_get_rag.return_value = mock_rag

            mock_response = Mock()
            mock_response.content = "Test answer"
            mock_llm_instance = Mock()
            mock_llm_instance.invoke.return_value = mock_response
            mock_llm.return_value = mock_llm_instance

            state = create_initial_state(user_request="What is X?", mode="ask")
            result = qa_node(state)

            assert "messages" in result
            print(f"[OK] QA node returned: {result['messages'][0].content}")

        # Test 2: Planner Node with mocks
        print("\n[2/2] Testing Planner Node (mocked)...")
        print("-" * 70)

        with patch('src.agents.planner_node.CrewFactory') as mock_factory_class:
            mock_plan = Plan(steps=["Step 1", "Step 2", "Step 3"])
            mock_result = Mock()
            mock_result.pydantic = mock_plan

            mock_crew = Mock()
            mock_crew.kickoff.return_value = mock_result

            mock_factory = Mock()
            mock_factory.create_planner_crew.return_value = mock_crew
            mock_factory_class.return_value = mock_factory

            state = create_initial_state(user_request="Add motor control", mode="plan")
            result = planner_node(state)

            assert "plan" in result
            assert len(result["plan"]) == 3
            print(f"[OK] Planner node returned {len(result['plan'])} steps")

        print("\n" + "="*70)
        print("[SUCCESS] ALL MANUAL TESTS PASSED")
        print("="*70)
        print("\nTo run FULL test suite:")
        print("  pytest tests/test_nodes.py -v")
        print("\nTo run INTEGRATION tests (requires API key, incurs costs):")
        print("  pytest tests/test_nodes.py -v -m integration")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_manual_tests()
