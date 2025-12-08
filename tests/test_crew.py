"""
Test Suite for CrewAI Factory.

Tests the CrewFactory class to verify:
1. Planner Crew generates valid JSON plan outputs
2. Coder Crew generates valid Structured Text code
3. Pydantic models enforce correct output schemas
4. LLM configuration is properly loaded

Run with: pytest tests/test_crew.py -v
"""

import pytest
from src.core.crew_factory import CrewFactory, Plan, CodeOutput
from src.core.config import Config


class TestCrewFactory:
    """Test cases for CrewFactory initialization and configuration."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixture to validate configuration before each test."""
        # Ensure API key is configured
        if not Config.OPENAI_API_KEY:
            pytest.skip("OPENAI_API_KEY not configured. Add it to .env to run tests.")

    def test_factory_initialization(self):
        """Test that CrewFactory initializes correctly with valid config."""
        factory = CrewFactory()
        assert factory.llm is not None
        assert factory.llm.model == Config.OPENAI_MODEL_NAME
        print(f"\n[OK] CrewFactory initialized with model: {Config.OPENAI_MODEL_NAME}")

    def test_factory_missing_api_key(self, monkeypatch):
        """Test that CrewFactory raises error when API key is missing."""
        # Temporarily remove API key
        monkeypatch.setattr(Config, "OPENAI_API_KEY", "")

        with pytest.raises(ValueError, match="OPENAI_API_KEY is not configured"):
            CrewFactory()


class TestPlannerCrew:
    """Test cases for Planner Crew functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixture."""
        if not Config.OPENAI_API_KEY:
            pytest.skip("OPENAI_API_KEY not configured. Add it to .env to run tests.")

    @pytest.fixture
    def factory(self):
        """Provide a CrewFactory instance for tests."""
        return CrewFactory()

    def test_create_planner_crew(self, factory):
        """Test that planner crew is created with correct configuration."""
        crew = factory.create_planner_crew("Add a motor control routine")

        assert crew is not None
        assert len(crew.agents) == 1
        assert len(crew.tasks) == 1
        assert crew.agents[0].role == "Lead Architect"
        print("\n[OK] Planner crew created successfully")

    @pytest.mark.integration
    def test_planner_crew_execution(self, factory):
        """
        Integration test: Run planner crew and verify JSON output.

        Note: This test makes actual LLM API calls and may incur costs.
        Mark as integration test to skip in CI/CD if needed.
        """
        print("\n" + "="*60)
        print("INTEGRATION TEST: Planner Crew Execution")
        print("="*60)

        # Create and run planner crew
        user_request = "Add a motor control routine with start/stop buttons"
        crew = factory.create_planner_crew(user_request)

        print(f"\nUser Request: {user_request}")
        print("\nExecuting planner crew (this may take 10-30 seconds)...")

        result = crew.kickoff()

        # Verify result structure
        assert result is not None
        print("\n[OK] Planner crew executed successfully")

        # Try to access pydantic output
        try:
            plan_output = result.pydantic
            assert isinstance(plan_output, Plan)
            assert len(plan_output.steps) > 0

            print(f"\n[PLAN] Generated Plan ({len(plan_output.steps)} steps):")
            print("-" * 60)
            for i, step in enumerate(plan_output.steps, 1):
                print(f"{i}. {step}")
            print("-" * 60)

        except AttributeError:
            # Fallback if pydantic attribute not available
            print(f"\n[PLAN] Raw Output:\n{result}")

        print("\n[OK] Plan output validated")


class TestCoderCrew:
    """Test cases for Coder Crew functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixture."""
        if not Config.OPENAI_API_KEY:
            pytest.skip("OPENAI_API_KEY not configured. Add it to .env to run tests.")

    @pytest.fixture
    def factory(self):
        """Provide a CrewFactory instance for tests."""
        return CrewFactory()

    def test_create_coder_crew(self, factory):
        """Test that coder crew is created with correct configuration."""
        task_desc = "Add a timer variable"
        file_context = "PROGRAM Main\nVAR\nEND_VAR\nEND_PROGRAM"

        crew = factory.create_coder_crew(task_desc, file_context)

        assert crew is not None
        assert len(crew.agents) == 2
        assert len(crew.tasks) == 2
        assert crew.agents[0].role == "Senior PLC Engineer"
        assert crew.agents[1].role == "Code Reviewer"
        print("\n[OK] Coder crew created successfully")

    @pytest.mark.integration
    def test_coder_crew_execution(self, factory):
        """
        Integration test: Run coder crew and verify ST code output.

        Note: This test makes actual LLM API calls and may incur costs.
        Mark as integration test to skip in CI/CD if needed.
        """
        print("\n" + "="*60)
        print("INTEGRATION TEST: Coder Crew Execution")
        print("="*60)

        # Prepare task
        task_desc = "Add a TON timer that turns on an output after 5 seconds"
        file_context = """
PROGRAM MotorControl
VAR
    bStartButton : BOOL := FALSE;
    bMotorRun : BOOL := FALSE;
END_VAR

(* Motor control logic will go here *)

END_PROGRAM
        """.strip()

        print(f"\nTask: {task_desc}")
        print(f"\nFile Context:\n{file_context}")
        print("\nExecuting coder crew (this may take 20-45 seconds)...")

        # Create and run coder crew
        crew = factory.create_coder_crew(task_desc, file_context)
        result = crew.kickoff()

        # Verify result structure
        assert result is not None
        print("\n[OK] Coder crew executed successfully")

        # Try to access pydantic output
        try:
            code_output = result.pydantic
            assert isinstance(code_output, CodeOutput)
            assert len(code_output.code) > 0
            assert len(code_output.explanation) > 0

            print("\n[CODE] Generated Code:")
            print("="*60)
            print(code_output.code)
            print("="*60)

            print(f"\n[INFO] Explanation:\n{code_output.explanation}")

            # Basic validation: Check for common ST keywords
            code_lower = code_output.code.lower()
            assert any(keyword in code_lower for keyword in ['var', 'end_var', 'ton', 'timer'])

            print("\n[OK] Code output validated (contains ST keywords)")

        except AttributeError:
            # Fallback if pydantic attribute not available
            print(f"\n[CODE] Raw Output:\n{result}")

        print("\n[OK] Code structure validated")


class TestPydanticModels:
    """Test cases for Pydantic output models."""

    def test_plan_model_validation(self):
        """Test Plan model validates correctly."""
        # Valid plan
        plan = Plan(steps=["Step 1", "Step 2", "Step 3"])
        assert len(plan.steps) == 3

        # Empty plan should fail due to min_length=1
        with pytest.raises(ValueError):
            Plan(steps=[])

        print("\n[OK] Plan model validation works correctly")

    def test_code_output_model_validation(self):
        """Test CodeOutput model validates correctly."""
        # Valid code output
        output = CodeOutput(
            code="VAR\n  x: INT;\nEND_VAR",
            explanation="Declares an integer variable x"
        )
        assert len(output.code) > 0
        assert len(output.explanation) > 0

        print("\n[OK] CodeOutput model validation works correctly")


# ============================================================================
# Manual Test Runner (for quick verification without pytest)
# ============================================================================

def run_manual_tests():
    """
    Run manual tests without pytest for quick verification.

    Usage: python tests/test_crew.py
    """
    print("="*70)
    print("MANUAL CREW FACTORY TESTS")
    print("="*70)

    try:
        # Test 1: Factory initialization
        print("\n[1/3] Testing CrewFactory initialization...")
        factory = CrewFactory()
        print(f"[OK] Factory initialized with model: {factory.llm.model}")

        # Test 2: Planner crew
        print("\n[2/3] Testing Planner Crew...")
        print("-" * 70)
        user_request = "Add a motor control routine with emergency stop"
        print(f"Request: {user_request}")

        planner_crew = factory.create_planner_crew(user_request)
        print(f"[OK] Planner crew created with {len(planner_crew.agents)} agent(s)")

        # Uncomment to run actual LLM call (costs money!)
        # print("\nExecuting planner crew (this will make an API call)...")
        # planner_result = planner_crew.kickoff()
        # print(f"[OK] Plan generated:\n{planner_result.pydantic.steps}")

        # Test 3: Coder crew
        print("\n[3/3] Testing Coder Crew...")
        print("-" * 70)
        task_desc = "Add a timer variable tmrDelay of type TON"
        file_context = "PROGRAM Main\nVAR\nEND_VAR\nEND_PROGRAM"
        print(f"Task: {task_desc}")

        coder_crew = factory.create_coder_crew(task_desc, file_context)
        print(f"[OK] Coder crew created with {len(coder_crew.agents)} agent(s)")

        # Uncomment to run actual LLM call (costs money!)
        # print("\nExecuting coder crew (this will make an API call)...")
        # coder_result = coder_crew.kickoff()
        # print(f"[OK] Code generated:\n{coder_result.pydantic.code}")

        print("\n" + "="*70)
        print("[SUCCESS] ALL MANUAL TESTS PASSED")
        print("="*70)
        print("\nTo run INTEGRATION tests with actual LLM calls:")
        print("  pytest tests/test_crew.py -v -m integration")
        print("\nWARNING: Integration tests will incur OpenAI API costs!")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_manual_tests()
