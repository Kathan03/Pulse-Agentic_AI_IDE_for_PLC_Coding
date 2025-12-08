# LangGraph + CrewAI Crash Course: Zero to Hero

**A Comprehensive Guide for Building Agentic AI Systems in Pulse**

---

## Table of Contents

1. [Introduction](#introduction)
2. [Part 1: Understanding LangGraph](#part-1-understanding-langgraph)
3. [Part 2: Understanding CrewAI](#part-2-understanding-crewai)
4. [Part 3: Integration Architecture](#part-3-integration-architecture)
5. [Part 4: Pulse Implementation](#part-4-pulse-implementation)
6. [Part 5: Advanced Patterns](#part-5-advanced-patterns)
7. [Resources](#resources)

---

## Introduction

### What Are We Building?

**Pulse** is an AI-powered IDE for PLC (Programmable Logic Controller) programming. It uses multiple AI agents working together to:
- Plan complex automation tasks
- Generate safe Structured Text code
- Test and validate implementations
- Answer user questions about the codebase

### Why Two Frameworks?

We use **two complementary frameworks**:

| Framework | Purpose | Metaphor |
|-----------|---------|----------|
| **LangGraph** | Orchestration & Workflow | The "traffic controller" managing agent flow |
| **CrewAI** | Task Execution | The "work teams" doing specialized tasks |

**Key Insight:** LangGraph manages the **WHAT and WHEN** (which agent runs next), while CrewAI handles the **HOW** (how to execute complex tasks).

---

## Part 1: Understanding LangGraph

### 1.1 What is LangGraph?

**LangGraph** is a framework for building **stateful, multi-agent workflows** using graphs.

Think of it as a **state machine** where:
- **Nodes** = Actions (run an agent, make a decision)
- **Edges** = Transitions (move from one action to the next)
- **State** = Shared memory that flows through the graph

### 1.2 Core Concepts

#### **1. State**

State is a **shared data structure** that flows through your graph. It's like a "clipboard" that every node can read from and write to.

**Example:**
```python
from typing import TypedDict, List

class PulseState(TypedDict):
    """State schema for Pulse IDE workflow."""
    user_request: str           # What the user asked for
    plan_steps: List[str]       # Generated plan
    code_changes: dict          # Files modified
    test_results: dict          # Validation results
    mode: str                   # "agent", "plan", or "ask"
```

**Key Properties:**
- **Typed:** Uses TypedDict or Pydantic for validation
- **Immutable:** Nodes return new state, not modify existing
- **Persistent:** State can be saved/loaded from database

#### **2. Nodes**

Nodes are **functions that transform state**.

**Signature:**
```python
def node_function(state: PulseState) -> PulseState:
    # Do work
    # Modify state
    return updated_state
```

**Example:**
```python
def planner_node(state: PulseState) -> PulseState:
    """Convert user request into actionable plan."""
    # Extract user request
    user_request = state["user_request"]

    # Create a CrewAI planner crew (we'll cover this in Part 2)
    factory = CrewFactory()
    crew = factory.create_planner_crew(user_request)

    # Run the crew
    result = crew.kickoff()

    # Update state with plan
    state["plan_steps"] = result.pydantic.steps
    return state
```

#### **3. Edges**

Edges define **how to move between nodes**.

**Types:**

| Edge Type | Description | Use Case |
|-----------|-------------|----------|
| **Normal Edge** | Always go from A → B | Sequential steps |
| **Conditional Edge** | Choose next node based on state | Branching logic |
| **Entry Point** | Where the graph starts | Initial node |

**Example:**
```python
from langgraph.graph import StateGraph, END

# Create graph
graph = StateGraph(PulseState)

# Add nodes
graph.add_node("planner", planner_node)
graph.add_node("coder", coder_node)
graph.add_node("tester", tester_node)

# Add edges
graph.set_entry_point("planner")       # Start here
graph.add_edge("planner", "coder")     # planner → coder (always)
graph.add_edge("coder", "tester")      # coder → tester (always)
graph.add_edge("tester", END)          # tester → END (finish)

# Compile
app = graph.compile()
```

#### **4. Conditional Edges**

Conditional edges let you **branch based on state**.

**Example:**
```python
def route_by_mode(state: PulseState) -> str:
    """Decide which node to run next based on mode."""
    if state["mode"] == "agent":
        return "planner"  # Full workflow
    elif state["mode"] == "plan":
        return "planner_with_approval"
    elif state["mode"] == "ask":
        return "qa_agent"  # Skip to Q&A
    else:
        return END

# Add conditional edge
graph.add_conditional_edges(
    "start",  # From this node
    route_by_mode,  # Use this function to decide
    {
        "planner": "planner",
        "planner_with_approval": "planner_with_approval",
        "qa_agent": "qa_agent"
    }
)
```

### 1.3 LangGraph in Action

**Complete Example:**

```python
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

# 1. Define State
class PulseState(TypedDict):
    user_request: str
    plan_steps: List[str]
    code: str
    mode: str

# 2. Define Nodes
def planner_node(state: PulseState) -> PulseState:
    """Generate a plan."""
    state["plan_steps"] = ["Step 1", "Step 2", "Step 3"]
    return state

def coder_node(state: PulseState) -> PulseState:
    """Generate code from plan."""
    state["code"] = "PROGRAM Main\n...\nEND_PROGRAM"
    return state

def router(state: PulseState) -> str:
    """Route based on mode."""
    if state["mode"] == "agent":
        return "planner"
    else:
        return END

# 3. Build Graph
graph = StateGraph(PulseState)
graph.add_node("planner", planner_node)
graph.add_node("coder", coder_node)

graph.set_entry_point("router")
graph.add_conditional_edges("router", router, {
    "planner": "planner",
    END: END
})
graph.add_edge("planner", "coder")
graph.add_edge("coder", END)

# 4. Compile and Run
app = graph.compile()
result = app.invoke({
    "user_request": "Add motor control",
    "plan_steps": [],
    "code": "",
    "mode": "agent"
})

print(result["code"])
```

### 1.4 Key Benefits

1. **Visualization:** LangGraph can generate visual diagrams of your workflow
2. **State Management:** Built-in state persistence and checkpointing
3. **Debugging:** Inspect state at each node
4. **Flexibility:** Easy to add/remove nodes and change flow

---

## Part 2: Understanding CrewAI

### 2.1 What is CrewAI?

**CrewAI** is a framework for **multi-agent collaboration** on complex tasks.

Think of it as a **virtual team** where:
- **Agents** = Team members with specialized roles
- **Tasks** = Work items to complete
- **Crew** = The team orchestrator
- **Process** = How work flows (sequential, parallel, hierarchical)

### 2.2 Core Concepts

#### **1. Agents**

Agents are **AI personas** with specific expertise.

**Anatomy of an Agent:**
```python
from crewai import Agent
from crewai.llm import LLM

engineer = Agent(
    role="Senior PLC Engineer",  # Job title
    goal="Write safe IEC 61131-3 Structured Text code",  # Objective
    backstory=(  # Expertise & personality
        "You are a senior PLC programmer with 20+ years of experience. "
        "You write clean, maintainable code following best practices."
    ),
    llm=LLM(model="gpt-4o", api_key="..."),  # LLM to use
    verbose=True,  # Print thinking process
    allow_delegation=False  # Can't delegate to other agents
)
```

**Key Properties:**

| Property | Purpose | Example |
|----------|---------|---------|
| `role` | Agent's job title | "Senior PLC Engineer" |
| `goal` | What agent tries to achieve | "Write safe ST code" |
| `backstory` | Expertise and constraints | "20+ years, follows IEC 61131-3" |
| `llm` | Language model to use | GPT-4o, Claude, etc. |
| `tools` | Functions agent can call | [file_writer, validator] |
| `allow_delegation` | Can assign work to others | True/False |

#### **2. Tasks**

Tasks are **work items** assigned to agents.

**Anatomy of a Task:**
```python
from crewai import Task
from pydantic import BaseModel, Field

# Define output schema
class CodeOutput(BaseModel):
    code: str = Field(description="Final ST code")
    explanation: str = Field(description="What the code does")

# Create task
coding_task = Task(
    description=(
        "Implement a motor control routine with:\n"
        "- Start/Stop buttons\n"
        "- Emergency stop\n"
        "- Run indicator\n"
    ),
    expected_output="IEC 61131-3 Structured Text code",
    agent=engineer,  # Who does this task
    output_pydantic=CodeOutput  # Enforce output schema
)
```

**Key Properties:**

| Property | Purpose | Example |
|----------|---------|---------|
| `description` | What to do | "Implement motor control..." |
| `expected_output` | What result looks like | "Structured Text code" |
| `agent` | Who executes this | `engineer` |
| `output_pydantic` | Structured output schema | `CodeOutput` model |
| `context` | Previous task outputs | `[planning_task]` |

#### **3. Crews**

Crews are **teams** that execute tasks.

**Anatomy of a Crew:**
```python
from crewai import Crew, Process

crew = Crew(
    agents=[engineer, reviewer],  # Team members
    tasks=[coding_task, review_task],  # Work items
    process=Process.sequential,  # How to execute
    verbose=True  # Print progress
)

# Execute the crew
result = crew.kickoff()
print(result.pydantic.code)
```

**Execution Processes:**

| Process | Description | Use Case |
|---------|-------------|----------|
| `sequential` | Tasks run one after another | Pipeline (plan → code → test) |
| `hierarchical` | Manager assigns tasks | Complex delegation |
| `parallel` | Tasks run simultaneously | Independent work |

#### **4. Pydantic Output Models**

CrewAI uses **Pydantic** to enforce structured outputs.

**Why Pydantic?**
- **Type Safety:** Guarantees correct data structure
- **Validation:** Auto-validates fields
- **Documentation:** Self-documenting schemas
- **JSON Serialization:** Easy to save/load

**Example:**
```python
from pydantic import BaseModel, Field
from typing import List

class Plan(BaseModel):
    """Structured plan output."""
    steps: List[str] = Field(
        description="List of implementation steps",
        min_length=1  # At least one step required
    )

# In task
planning_task = Task(
    description="Break down this requirement into steps",
    expected_output="JSON with 'steps' field",
    agent=architect,
    output_pydantic=Plan  # Enforce schema
)

# Access structured output
result = crew.kickoff()
plan = result.pydantic  # This is a Plan object
print(plan.steps)  # ['Step 1', 'Step 2', ...]
```

### 2.3 CrewAI in Action

**Complete Example:**

```python
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
from pydantic import BaseModel, Field
from typing import List

# 1. Define output schema
class Plan(BaseModel):
    steps: List[str] = Field(min_length=1)

# 2. Create LLM
llm = LLM(model="gpt-4o", api_key="sk-...")

# 3. Create agent
architect = Agent(
    role="Lead Architect",
    goal="Break down requirements into steps",
    backstory="You're an expert at planning PLC projects.",
    llm=llm,
    verbose=True
)

# 4. Create task
planning_task = Task(
    description="Break down: 'Add motor control with emergency stop'",
    expected_output="List of implementation steps",
    agent=architect,
    output_pydantic=Plan
)

# 5. Create crew
crew = Crew(
    agents=[architect],
    tasks=[planning_task],
    process=Process.sequential,
    verbose=True
)

# 6. Execute
result = crew.kickoff()
print(result.pydantic.steps)
```

### 2.4 Multi-Agent Workflow

**Example: Code Generation with Review**

```python
# Agent 1: Engineer
engineer = Agent(
    role="Senior PLC Engineer",
    goal="Write safe ST code",
    backstory="Expert in IEC 61131-3",
    llm=llm
)

# Agent 2: Reviewer
reviewer = Agent(
    role="Code Reviewer",
    goal="Find and fix safety issues",
    backstory="Safety-critical systems auditor",
    llm=llm
)

# Task 1: Generate code
coding_task = Task(
    description="Implement motor control",
    expected_output="ST code",
    agent=engineer
)

# Task 2: Review code (gets output from Task 1)
review_task = Task(
    description="Review the code for safety issues",
    expected_output="Validated ST code",
    agent=reviewer,
    context=[coding_task],  # Gets engineer's output
    output_pydantic=CodeOutput
)

# Crew executes: engineer → reviewer
crew = Crew(
    agents=[engineer, reviewer],
    tasks=[coding_task, review_task],
    process=Process.sequential
)

result = crew.kickoff()
print(result.pydantic.code)  # Final reviewed code
```

---

## Part 3: Integration Architecture

### 3.1 Why Integrate LangGraph + CrewAI?

**The Problem:**
- **LangGraph alone:** Great for workflow, but struggles with complex multi-step reasoning within a single node
- **CrewAI alone:** Great for task execution, but lacks high-level workflow orchestration

**The Solution:**
Use LangGraph for **workflow orchestration** and CrewAI for **task execution within nodes**.

### 3.2 Architecture Pattern

**Pattern: LangGraph Node → CrewAI Crew → State Update**

```
┌─────────────────────────────────────────────────────────────┐
│ LangGraph Orchestration Layer                               │
│                                                              │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐          │
│  │ Planner  │ ───> │  Coder   │ ───> │  Tester  │          │
│  │  Node    │      │   Node   │      │   Node   │          │
│  └────┬─────┘      └────┬─────┘      └────┬─────┘          │
│       │                 │                  │                │
└───────┼─────────────────┼──────────────────┼────────────────┘
        │                 │                  │
        ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│ CrewAI Execution Layer                                      │
│                                                              │
│  ┌──────────┐      ┌──────────────────┐      ┌──────────┐  │
│  │ Architect│      │ Engineer+Reviewer│      │Validation│  │
│  │  Crew    │      │      Crew        │      │   Crew   │  │
│  └──────────┘      └──────────────────┘      └──────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Key Insights:**
1. Each **LangGraph node** can internally use a **CrewAI crew**
2. **State flows** through LangGraph nodes
3. **CrewAI crews** do the heavy lifting inside each node
4. **Pydantic models** ensure type safety at boundaries

### 3.3 Code Pattern

```python
# ============================================================================
# LangGraph Layer: Workflow Orchestration
# ============================================================================

from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PulseState(TypedDict):
    user_request: str
    plan_steps: List[str]
    code: str

# ============================================================================
# CrewAI Layer: Task Execution (inside nodes)
# ============================================================================

from src.core.crew_factory import CrewFactory

def planner_node(state: PulseState) -> PulseState:
    """LangGraph node that uses CrewAI internally."""
    # 1. Extract data from state
    user_request = state["user_request"]

    # 2. Create and execute CrewAI crew
    factory = CrewFactory()
    crew = factory.create_planner_crew(user_request)
    result = crew.kickoff()

    # 3. Update state with crew result
    state["plan_steps"] = result.pydantic.steps

    # 4. Return updated state
    return state

def coder_node(state: PulseState) -> PulseState:
    """Another node using a different CrewAI crew."""
    factory = CrewFactory()
    crew = factory.create_coder_crew(
        task_desc=state["plan_steps"][0],
        file_context=""
    )
    result = crew.kickoff()

    state["code"] = result.pydantic.code
    return state

# ============================================================================
# Build LangGraph Workflow
# ============================================================================

graph = StateGraph(PulseState)
graph.add_node("planner", planner_node)
graph.add_node("coder", coder_node)

graph.set_entry_point("planner")
graph.add_edge("planner", "coder")
graph.add_edge("coder", END)

app = graph.compile()

# ============================================================================
# Execute
# ============================================================================

result = app.invoke({
    "user_request": "Add motor control",
    "plan_steps": [],
    "code": ""
})

print(result["code"])
```

### 3.4 Benefits of This Pattern

| Benefit | Description |
|---------|-------------|
| **Separation of Concerns** | Workflow logic ≠ Task execution |
| **Testability** | Test LangGraph and CrewAI independently |
| **Modularity** | Swap out crews without changing workflow |
| **Type Safety** | Pydantic enforces contracts at boundaries |
| **Observability** | Debug workflow and agents separately |

---

## Part 4: Pulse Implementation

### 4.1 Project Architecture

**Directory Structure:**
```
Pulse/
├── src/
│   ├── core/
│   │   ├── state.py          # LangGraph state schema
│   │   ├── crew_factory.py   # CrewAI crew factory
│   │   └── config.py         # LLM configuration
│   ├── agents/
│   │   ├── graph.py          # LangGraph orchestration
│   │   ├── planner.py        # Planner node
│   │   ├── coder.py          # Coder node
│   │   └── tester.py         # Tester node
│   └── ui/
│       └── app.py            # Flet UI
```

### 4.2 State Schema (`src/core/state.py`)

**Future Implementation:**
```python
from typing import TypedDict, List, Optional
from pydantic import BaseModel

class PulseState(TypedDict):
    """
    Complete state schema for Pulse IDE workflow.

    This state flows through all LangGraph nodes.
    """
    # User inputs
    user_request: str
    mode: str  # "agent", "plan", or "ask"

    # Planner outputs
    plan_steps: List[str]
    plan_approved: bool

    # Coder outputs
    files_modified: dict  # {filename: content}
    code_changes: List[dict]

    # Tester outputs
    test_results: dict
    validation_passed: bool

    # QA outputs
    qa_response: Optional[str]

    # Metadata
    session_id: str
    workspace_path: str
```

### 4.3 CrewFactory Implementation (`src/core/crew_factory.py`)

**We've already implemented this!** Let's review the key parts:

```python
from crewai import Agent, Task, Crew, Process
from pydantic import BaseModel, Field
from typing import List

class Plan(BaseModel):
    """Output schema for planner crew."""
    steps: List[str] = Field(min_length=1)

class CrewFactory:
    def create_planner_crew(self, user_request: str) -> Crew:
        """Create a crew that generates implementation plans."""

        # Define agent
        architect = Agent(
            role="Lead Architect",
            goal="Break down PLC requirements into steps",
            backstory="Expert PLC systems architect...",
            llm=self.llm
        )

        # Define task
        planning_task = Task(
            description=f"Analyze: {user_request}",
            expected_output="JSON with steps",
            agent=architect,
            output_pydantic=Plan
        )

        # Return crew
        return Crew(
            agents=[architect],
            tasks=[planning_task],
            process=Process.sequential
        )

    def create_coder_crew(self, task_desc: str, file_context: str) -> Crew:
        """Create a crew that generates and reviews code."""

        # Two agents: Engineer + Reviewer
        engineer = Agent(
            role="Senior PLC Engineer",
            goal="Write safe ST code",
            backstory="20+ years experience...",
            llm=self.llm
        )

        reviewer = Agent(
            role="Code Reviewer",
            goal="Audit for safety issues",
            backstory="Safety-critical auditor...",
            llm=self.llm
        )

        # Two tasks: Code + Review
        coding_task = Task(
            description=f"Implement: {task_desc}\nContext: {file_context}",
            expected_output="ST code",
            agent=engineer
        )

        review_task = Task(
            description="Review and fix the code",
            expected_output="Validated ST code with explanation",
            agent=reviewer,
            context=[coding_task],
            output_pydantic=CodeOutput
        )

        # Return crew
        return Crew(
            agents=[engineer, reviewer],
            tasks=[coding_task, review_task],
            process=Process.sequential
        )
```

### 4.4 LangGraph Nodes (`src/agents/planner.py`)

**Future Implementation:**
```python
from src.core.state import PulseState
from src.core.crew_factory import CrewFactory

def planner_node(state: PulseState) -> PulseState:
    """
    Planner Node: Convert user request into plan.

    Uses CrewAI planner crew internally.
    """
    # Extract user request from state
    user_request = state["user_request"]

    # Create and execute planner crew
    factory = CrewFactory()
    crew = factory.create_planner_crew(user_request)
    result = crew.kickoff()

    # Update state with plan
    state["plan_steps"] = result.pydantic.steps

    # Log for debugging
    print(f"[PLANNER] Generated {len(state['plan_steps'])} steps")

    return state
```

### 4.5 LangGraph Orchestration (`src/agents/graph.py`)

**Future Implementation:**
```python
from langgraph.graph import StateGraph, END
from src.core.state import PulseState
from src.agents.planner import planner_node
from src.agents.coder import coder_node
from src.agents.tester import tester_node
from src.agents.qa import qa_node

def create_pulse_graph() -> StateGraph:
    """Create the main Pulse workflow graph."""

    graph = StateGraph(PulseState)

    # Add nodes
    graph.add_node("planner", planner_node)
    graph.add_node("coder", coder_node)
    graph.add_node("tester", tester_node)
    graph.add_node("qa", qa_node)

    # Routing logic
    def route_by_mode(state: PulseState) -> str:
        mode = state["mode"]
        if mode == "agent":
            return "planner"  # Full workflow
        elif mode == "plan":
            return "planner_with_approval"
        elif mode == "ask":
            return "qa"  # Skip to Q&A
        return END

    # Define edges
    graph.set_entry_point("router")
    graph.add_conditional_edges("router", route_by_mode, {
        "planner": "planner",
        "qa": "qa"
    })

    # Sequential flow: planner → coder → tester
    graph.add_edge("planner", "coder")
    graph.add_edge("coder", "tester")
    graph.add_edge("tester", END)
    graph.add_edge("qa", END)

    return graph.compile()
```

### 4.6 UI Integration (`src/ui/app.py`)

**Future Implementation:**
```python
import flet as ft
from src.agents.graph import create_pulse_graph

def main(page: ft.Page):
    # Create LangGraph app
    pulse_app = create_pulse_graph()

    def on_submit(e):
        user_request = chat_input.value
        mode = mode_selector.value

        # Execute LangGraph workflow
        result = pulse_app.invoke({
            "user_request": user_request,
            "mode": mode,
            "plan_steps": [],
            "files_modified": {},
            "workspace_path": "/path/to/workspace"
        })

        # Display results in UI
        chat_view.controls.append(
            ft.Text(f"Plan: {result['plan_steps']}")
        )
        page.update()

    # UI components
    chat_input = ft.TextField(label="Enter request")
    mode_selector = ft.Dropdown(
        options=["agent", "plan", "ask"],
        value="agent"
    )
    submit_button = ft.ElevatedButton("Run", on_click=on_submit)

    page.add(chat_input, mode_selector, submit_button)

ft.app(target=main)
```

---

## Part 5: Advanced Patterns

### 5.1 Human-in-the-Loop (Plan Mode)

**Challenge:** Get user approval before executing plan.

**Solution:**
```python
def planner_with_approval_node(state: PulseState) -> PulseState:
    """Generate plan and wait for approval."""
    # Generate plan
    factory = CrewFactory()
    crew = factory.create_planner_crew(state["user_request"])
    result = crew.kickoff()
    state["plan_steps"] = result.pydantic.steps

    # Display plan to user (via UI)
    display_plan(state["plan_steps"])

    # Wait for approval (blocking)
    approved = wait_for_user_approval()
    state["plan_approved"] = approved

    return state

def conditional_route_after_plan(state: PulseState) -> str:
    """Route based on approval."""
    if state["plan_approved"]:
        return "coder"  # Proceed
    else:
        return END  # Stop workflow

# In graph
graph.add_node("planner_with_approval", planner_with_approval_node)
graph.add_conditional_edges("planner_with_approval", conditional_route_after_plan, {
    "coder": "coder",
    END: END
})
```

### 5.2 Iterative Refinement

**Challenge:** Agent output isn't good enough on first try.

**Solution: Feedback Loop**
```python
def coder_node_with_retry(state: PulseState) -> PulseState:
    """Generate code with iterative refinement."""
    max_attempts = 3

    for attempt in range(max_attempts):
        # Generate code
        factory = CrewFactory()
        crew = factory.create_coder_crew(
            state["plan_steps"][0],
            state.get("file_context", "")
        )
        result = crew.kickoff()

        # Validate code
        if validate_code(result.pydantic.code):
            state["code"] = result.pydantic.code
            return state

        # Add feedback to context for next attempt
        state["file_context"] += f"\n\nPrevious attempt failed validation."

    # If all attempts fail
    state["code"] = "ERROR: Could not generate valid code"
    return state
```

### 5.3 Parallel Execution

**Challenge:** Run multiple independent crews concurrently.

**Solution: Use CrewAI Parallel Process**
```python
from crewai import Process

def create_parallel_analysis_crew() -> Crew:
    """Create a crew with parallel tasks."""

    # Three independent analysts
    safety_analyst = Agent(role="Safety Analyst", ...)
    performance_analyst = Agent(role="Performance Analyst", ...)
    style_analyst = Agent(role="Style Analyst", ...)

    # Three independent tasks
    safety_task = Task(agent=safety_analyst, ...)
    performance_task = Task(agent=performance_analyst, ...)
    style_task = Task(agent=style_analyst, ...)

    # Run in parallel
    return Crew(
        agents=[safety_analyst, performance_analyst, style_analyst],
        tasks=[safety_task, performance_task, style_task],
        process=Process.parallel  # ← Key difference
    )
```

### 5.4 RAG Integration

**Challenge:** Agents need access to codebase context.

**Solution: Add RAG Tool to Agents**
```python
from crewai import Agent, Tool

def create_rag_tool():
    """Create a RAG retrieval tool."""
    def search_codebase(query: str) -> str:
        # Use Chroma vector store
        from src.core.rag import query_rag
        results = query_rag(query, top_k=5)
        return "\n".join([r.content for r in results])

    return Tool(
        name="search_codebase",
        description="Search the codebase for relevant code snippets",
        func=search_codebase
    )

# Add tool to agent
qa_agent = Agent(
    role="QA Engineer",
    goal="Answer questions about the codebase",
    tools=[create_rag_tool()],  # ← Agent can now search codebase
    llm=llm
)
```

### 5.5 Persistence & Resumability

**Challenge:** Save workflow state to database.

**Solution: LangGraph Checkpointing**
```python
from langgraph.checkpoint.sqlite import SqliteSaver

# Create checkpointer
checkpointer = SqliteSaver.from_conn_string("pulse.db")

# Compile graph with checkpointing
app = graph.compile(checkpointer=checkpointer)

# Run with thread_id for persistence
result = app.invoke(
    {"user_request": "Add motor", ...},
    config={"configurable": {"thread_id": "session-123"}}
)

# Later: Resume from checkpoint
resumed_result = app.invoke(
    {"user_request": "Continue..."},
    config={"configurable": {"thread_id": "session-123"}}
)
```

---

## Part 6: Best Practices

### 6.1 State Design

**DO:**
- Use TypedDict or Pydantic for state schema
- Keep state flat and simple
- Document each field with comments

**DON'T:**
- Store large objects in state (use references/IDs)
- Mutate state in-place (always return new state)
- Use state as a database (persist externally)

### 6.2 Agent Design

**DO:**
- Give agents clear, specific roles
- Write detailed backstories (guides behavior)
- Use `output_pydantic` for structured outputs
- Limit delegation (simpler is better)

**DON'T:**
- Create overly generic agents
- Use vague goals like "help the user"
- Assume agents will "figure it out"

### 6.3 Task Design

**DO:**
- Provide concrete examples in task description
- Use `context` to pass previous task outputs
- Validate outputs with Pydantic models
- Keep tasks focused (one job per task)

**DON'T:**
- Write ambiguous task descriptions
- Assume agents have implicit context
- Skip output validation

### 6.4 Graph Design

**DO:**
- Start simple (linear flow first)
- Add conditional routing only when needed
- Test each node independently
- Visualize your graph (use LangGraph Studio)

**DON'T:**
- Over-engineer with complex branching
- Create circular dependencies
- Skip error handling

---

## Part 7: Debugging Tips

### 7.1 LangGraph Debugging

**Enable Verbose Mode:**
```python
graph = StateGraph(PulseState)
# ... add nodes and edges
app = graph.compile(debug=True)
```

**Inspect State at Each Node:**
```python
def debug_node(state: PulseState) -> PulseState:
    print(f"[DEBUG] State: {state}")
    # ... rest of node logic
    return state
```

**Use LangSmith (Optional):**
```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "..."
```

### 7.2 CrewAI Debugging

**Enable Verbose Output:**
```python
crew = Crew(
    agents=[agent1, agent2],
    tasks=[task1, task2],
    verbose=True  # ← Shows agent thinking process
)
```

**Test Agents Individually:**
```python
# Test just the agent's response
test_task = Task(
    description="Simple test task",
    agent=engineer,
    expected_output="Test output"
)
test_crew = Crew(agents=[engineer], tasks=[test_task])
result = test_crew.kickoff()
print(result)
```

### 7.3 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "KeyError in state" | Missing state field | Initialize all fields in state schema |
| "Pydantic validation error" | LLM output doesn't match schema | Improve task description, add examples |
| "Agent not following instructions" | Vague backstory/goal | Make agent role more specific |
| "Workflow stuck in loop" | Bad conditional routing | Check routing logic, add exit conditions |
| "Slow execution" | Too many LLM calls | Reduce agent delegation, simplify tasks |

---

## Part 8: Testing

### 8.1 Unit Testing CrewAI

```python
import pytest
from src.core.crew_factory import CrewFactory

def test_planner_crew_creation():
    """Test that planner crew is created correctly."""
    factory = CrewFactory()
    crew = factory.create_planner_crew("Add motor")

    assert len(crew.agents) == 1
    assert crew.agents[0].role == "Lead Architect"
    assert len(crew.tasks) == 1

@pytest.mark.integration
def test_planner_crew_execution():
    """Test actual LLM call (integration test)."""
    factory = CrewFactory()
    crew = factory.create_planner_crew("Add emergency stop")
    result = crew.kickoff()

    assert result.pydantic is not None
    assert len(result.pydantic.steps) > 0
```

### 8.2 Unit Testing LangGraph

```python
from src.core.state import PulseState
from src.agents.planner import planner_node

def test_planner_node():
    """Test planner node updates state correctly."""
    # Arrange
    initial_state: PulseState = {
        "user_request": "Add motor control",
        "plan_steps": [],
        "mode": "agent"
    }

    # Act
    result_state = planner_node(initial_state)

    # Assert
    assert len(result_state["plan_steps"]) > 0
    assert result_state["user_request"] == initial_state["user_request"]
```

### 8.3 Integration Testing

```python
def test_full_workflow():
    """Test complete LangGraph + CrewAI workflow."""
    from src.agents.graph import create_pulse_graph

    app = create_pulse_graph()

    result = app.invoke({
        "user_request": "Add a motor with start/stop buttons",
        "mode": "agent",
        "plan_steps": [],
        "code": ""
    })

    assert len(result["plan_steps"]) > 0
    assert len(result["code"]) > 0
    assert "PROGRAM" in result["code"]
```

---

## Resources

### Official Documentation

**LangGraph:**
- [Official Docs](https://langchain-ai.github.io/langgraph/)
- [Tutorial](https://langchain-ai.github.io/langgraph/tutorials/introduction/)
- [Examples](https://github.com/langchain-ai/langgraph/tree/main/examples)
- [API Reference](https://langchain-ai.github.io/langgraph/reference/)

**CrewAI:**
- [Official Docs](https://docs.crewai.com/)
- [Quickstart](https://docs.crewai.com/quickstart)
- [Examples](https://github.com/joaomdmoura/crewAI-examples)
- [API Reference](https://docs.crewai.com/api-reference)

### Key Concepts Summary

| Concept | LangGraph | CrewAI |
|---------|-----------|--------|
| **Core Unit** | Node (function) | Agent (AI persona) |
| **Orchestration** | Graph (state machine) | Crew (team) |
| **State Management** | TypedDict flowing through nodes | Task context & output |
| **Routing** | Conditional edges | Process type (sequential/parallel) |
| **Output** | Updated state | Pydantic models |

### When to Use What

| Use Case | Framework | Why |
|----------|-----------|-----|
| Multi-step workflow | LangGraph | State management, routing |
| Complex task with multiple sub-steps | CrewAI | Multi-agent collaboration |
| Human-in-the-loop | LangGraph | Conditional routing, persistence |
| Iterative refinement | CrewAI | Agent delegation, context sharing |
| RAG + Agents | Both | LangGraph orchestrates, CrewAI executes with tools |

---

## Conclusion

**You've learned:**
1. **LangGraph** for workflow orchestration using state machines
2. **CrewAI** for multi-agent task execution
3. **Integration pattern** combining both frameworks
4. **Pulse architecture** implementing this pattern
5. **Advanced patterns** (human-in-loop, RAG, persistence)
6. **Best practices** for production systems

**Next Steps:**
1. Review the code in `src/core/crew_factory.py`
2. Implement `src/agents/graph.py` with LangGraph orchestration
3. Test the integration with `tests/test_crew.py`
4. Build the UI integration in `src/ui/app.py`

**Remember:**
- **LangGraph = WHAT/WHEN** (which agent, when to run)
- **CrewAI = HOW** (how to execute complex tasks)
- **Integration = Best of both worlds**

---

**Happy Building!** 🚀
