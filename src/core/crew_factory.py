"""
CrewAI Factory Module for Pulse IDE.

Provides factory methods to instantiate specialized AI crews for:
- Planning (Breaking down user requests into actionable steps)
- Coding (Generating safe IEC 61131-3 Structured Text code)

Each crew is configured with agents, tasks, and LLM settings from the
application configuration.
"""

import os
from typing import List
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM

from src.core.config import Config


# ============================================================================
# Pydantic Models for Structured Outputs
# ============================================================================

class Plan(BaseModel):
    """
    Structured output model for the Planner Agent.

    Attributes:
        steps: Ordered list of atomic file-modification steps.
    """
    steps: List[str] = Field(
        description="List of actionable steps to implement the user's request",
        min_length=1
    )


class CodeOutput(BaseModel):
    """
    Structured output model for the Coder Agent.

    Attributes:
        code: Final reviewed IEC 61131-3 Structured Text code.
        explanation: Brief explanation of what the code does.
    """
    code: str = Field(
        description="Final Structured Text code block (no markdown, just code)"
    )
    explanation: str = Field(
        description="Brief explanation of the implementation"
    )


# ============================================================================
# CrewFactory Class
# ============================================================================

class CrewFactory:
    """
    Factory class for creating specialized AI crews.

    This class instantiates CrewAI crews configured with:
    - LLM settings from application config
    - Specialized agents for planning and coding
    - Structured output schemas using Pydantic models

    Usage:
        factory = CrewFactory()
        planner_crew = factory.create_planner_crew("Add a motor control routine")
        result = planner_crew.kickoff()
    """

    def __init__(self):
        """
        Initialize the CrewFactory.

        Sets up environment variables required by CrewAI internals
        and validates configuration.
        """
        # Validate configuration
        if not Config.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not configured. "
                "Please set it in your .env file."
            )

        # Set environment variable for CrewAI internals
        os.environ["OPENAI_API_KEY"] = Config.OPENAI_API_KEY

        # Store LLM configuration
        self.llm = LLM(
            model=Config.OPENAI_MODEL_NAME,
            api_key=Config.OPENAI_API_KEY
        )

    def create_planner_crew(self, user_request: str) -> Crew:
        """
        Create a Planner Crew to convert user requests into structured plans.

        The Planner Crew analyzes user requirements and breaks them down into
        atomic, actionable file-modification steps. The output is guaranteed
        to be valid JSON conforming to the Plan schema.

        Args:
            user_request: Natural language description of what the user wants.

        Returns:
            Crew: Configured planner crew ready to execute.

        Example:
            >>> factory = CrewFactory()
            >>> crew = factory.create_planner_crew("Add emergency stop logic")
            >>> result = crew.kickoff()
            >>> print(result.pydantic.steps)
        """
        # Define the Lead Architect agent
        architect = Agent(
            role="Lead Architect",
            goal="Break down PLC automation requirements into atomic file-modification steps",
            backstory=(
                "You are an expert PLC systems architect with 20+ years of experience "
                "in industrial automation. You excel at decomposing complex control logic "
                "into clear, implementable steps. You think in terms of IEC 61131-3 "
                "programming standards and always consider safety, timing, and modularity."
            ),
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

        # Define the planning task
        planning_task = Task(
            description=(
                f"Analyze the following user request and create a detailed implementation plan:\n\n"
                f"REQUEST: {user_request}\n\n"
                f"Break this down into atomic, actionable steps. Each step should:\n"
                f"1. Be specific about which file(s) to modify\n"
                f"2. Describe the exact change needed (e.g., 'Add FUNCTION_BLOCK MotorControl to main.st')\n"
                f"3. Consider dependencies (e.g., 'Declare variable before using it')\n"
                f"4. Address safety concerns (e.g., 'Add emergency stop check')\n\n"
                f"Return a structured list of steps that a PLC programmer can follow sequentially."
            ),
            expected_output=(
                "A JSON object with a 'steps' field containing an ordered list of "
                "actionable implementation steps."
            ),
            agent=architect,
            output_pydantic=Plan
        )

        # Create and return the crew
        return Crew(
            agents=[architect],
            tasks=[planning_task],
            process=Process.sequential,
            verbose=True
        )

    def create_coder_crew(self, task_desc: str, file_context: str) -> Crew:
        """
        Create a Coder Crew to generate safe IEC 61131-3 Structured Text code.

        The Coder Crew uses a two-agent workflow:
        1. Senior PLC Engineer: Generates initial implementation
        2. Code Reviewer: Audits and fixes safety/syntax issues

        Args:
            task_desc: Description of the coding task to implement.
            file_context: Current file content or relevant context for the task.

        Returns:
            Crew: Configured coder crew ready to execute.

        Example:
            >>> factory = CrewFactory()
            >>> context = "PROGRAM Main\\nVAR\\nEND_VAR\\nEND_PROGRAM"
            >>> crew = factory.create_coder_crew("Add a timer variable", context)
            >>> result = crew.kickoff()
            >>> print(result.pydantic.code)
        """
        # Agent 1: Senior PLC Engineer
        engineer = Agent(
            role="Senior PLC Engineer",
            goal="Write safe, efficient IEC 61131-3 Structured Text code with no markdown formatting",
            backstory=(
                "You are a senior PLC programmer with deep expertise in IEC 61131-3 standards. "
                "You write clean, maintainable Structured Text code that follows best practices: "
                "- Clear variable naming (e.g., bMotorRun, tmrDelay) "
                "- Proper data typing (BOOL, INT, TIME) "
                "- Safe initialization of variables "
                "- No infinite loops or unsafe operations "
                "- Comments only where logic is non-obvious "
                "You NEVER use markdown formatting - you output pure ST code only."
            ),
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

        # Agent 2: Code Reviewer
        reviewer = Agent(
            role="Code Reviewer",
            goal="Audit PLC code for safety issues, syntax errors, and missing variable declarations",
            backstory=(
                "You are a safety-critical systems auditor specializing in PLC code review. "
                "You meticulously check for: "
                "- Infinite loops or timing issues "
                "- Uninitialized variables "
                "- Type mismatches "
                "- Missing emergency stop logic "
                "- Syntax errors "
                "You take the engineer's code and return ONLY the final, validated code block - "
                "no explanations, no markdown, just pure ST code."
            ),
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

        # Task 1: Generate initial code
        coding_task = Task(
            description=(
                f"Implement the following task:\n\n"
                f"TASK: {task_desc}\n\n"
                f"CURRENT FILE CONTEXT:\n{file_context}\n\n"
                f"REQUIREMENTS:\n"
                f"- Use IEC 61131-3 Structured Text syntax\n"
                f"- Follow naming conventions (bBool, iInt, tmrTimer, etc.)\n"
                f"- Initialize all variables with safe defaults\n"
                f"- Add brief comments only where logic is complex\n"
                f"- Output ONLY the Structured Text code - no markdown, no explanations\n\n"
                f"Generate the code now."
            ),
            expected_output="Pure IEC 61131-3 Structured Text code with no markdown formatting",
            agent=engineer
        )

        # Task 2: Review and fix the code
        review_task = Task(
            description=(
                "Review the code generated by the Senior PLC Engineer. Check for:\n"
                "1. Syntax errors (missing semicolons, incorrect keywords)\n"
                "2. Safety issues (infinite loops, unguarded operations)\n"
                "3. Missing variable declarations\n"
                "4. Type mismatches\n"
                "5. Timing concerns (scan cycle impact)\n\n"
                "Fix any issues you find and return ONLY the final, production-ready code block. "
                "No explanations, no markdown formatting - just the validated ST code."
            ),
            expected_output=(
                "A JSON object with 'code' (final validated ST code) and "
                "'explanation' (brief description of what the code does)"
            ),
            agent=reviewer,
            output_pydantic=CodeOutput,
            context=[coding_task]  # Reviewer gets engineer's output as context
        )

        # Create and return the crew
        return Crew(
            agents=[engineer, reviewer],
            tasks=[coding_task, review_task],
            process=Process.sequential,
            verbose=True
        )


# ============================================================================
# Module Exports
# ============================================================================

__all__ = ["CrewFactory", "Plan", "CodeOutput"]
