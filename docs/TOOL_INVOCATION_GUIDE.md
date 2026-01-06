# Tool Invocation Guide for Pulse IDE

**Version:** 2.6
**Last Updated:** 2025-12-29

This guide explains how the Master Agent invokes tools and how the Tool Belt architecture works in Pulse IDE.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INPUT                              │
│                   (via Pulse Chat)                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  MASTER AGENT (The Brain)                    │
│                                                              │
│  • Analyzes user request                                    │
│  • Decides which tool(s) to use                             │
│  • Calls LLM with function calling                          │
│  • Receives tool call decision from LLM                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                TOOL EXECUTION NODE (The Hands)               │
│                                                              │
│  • Checks if tool requires approval                         │
│  • Pauses graph for user approval (if needed)              │
│  • Executes tool via ToolRegistry                           │
│  • Returns result to Master Agent                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 TOOL BELT (3 Tiers)                          │
│                                                              │
│  Tier 1: Atomic (fast, deterministic)                       │
│  Tier 2: Permissioned (requires approval)                   │
│  Tier 3: Intelligence (web search + subsystems)             │
└─────────────────────────────────────────────────────────────┘
```

---

## How Function Calling Works

### Step 1: User Input
```
User types in Pulse Chat: "create test.txt"
```

### Step 2: Master Agent Analysis
The Master Agent node (`master_agent_node`) is called:

1. **Load system prompt** based on mode (Agent/Ask/Plan)
2. **Enhance prompt** if .st files detected (PLC specialization)
3. **Get tool schemas** from ToolRegistry
4. **Call LLM** with conversation history + tool schemas

**Code location:** `src/agents/master_graph.py:143-341`

### Step 3: LLM Function Calling
The LLM (OpenAI or Anthropic) responds with:

```json
{
  "tool_calls": [
    {
      "id": "call_abc123",
      "name": "manage_file_ops",
      "arguments": {
        "operation": "create",
        "path": "test.txt",
        "content": ""
      }
    }
  ]
}
```

**Code location:** `src/core/llm_client.py:341-380`

### Step 4: Tool Execution
The tool_execution_node receives the tool call:

1. **Check approval requirement:**
   - `apply_patch` → requires approval
   - `plan_terminal_cmd` → requires approval
   - `manage_file_ops` → no approval needed

2. **Execute tool:**
   - Call `ToolRegistry.invoke_tool(tool_name, args)`
   - Tool wrapper calls actual implementation
   - Result returned as `ToolOutput`

**Code location:** `src/agents/master_graph.py:348-611`

### Step 5: Result Returned
The ToolOutput is added to the message history and the graph loops back to Master Agent, which can:
- Call another tool (multi-step workflow)
- Provide a direct answer to the user
- End the conversation

---

## Tool Belt: 3-Tier Architecture

### Tier 1: Atomic Tools (Fast, Deterministic)

#### 1.1 `manage_file_ops`
**Purpose:** Create, read, update, delete, or list files

**Function signature:**
```python
def manage_file_ops(
    operation: str,  # "create", "read", "update", "delete", "list"
    path: str,
    project_root: Path,
    content: Optional[str] = None,
    rag_manager: Optional[RAGManager] = None
) -> Dict[str, Any]
```

**Example invocation:**
```python
# LLM requests:
{
  "tool": "manage_file_ops",
  "args": {
    "operation": "create",
    "path": "test.txt",
    "content": "Hello, World!"
  }
}

# Tool registry calls:
result = manage_file_ops(
    operation="create",
    path="test.txt",
    project_root=Path("/workspace"),
    content="Hello, World!",
    rag_manager=rag_manager
)

# Returns:
{
    "status": "success",
    "path": "test.txt",
    "message": "File created successfully"
}
```

**Implementation:** `src/tools/file_ops.py`

#### 1.2 `apply_patch`
**Purpose:** Generate and preview unified diff patches

**Function signature:**
```python
def preview_patch(
    diff: str,  # Unified diff format
    project_root: Path
) -> PatchPlan
```

**Example invocation:**
```python
# LLM requests:
{
  "tool": "apply_patch",
  "args": {
    "diff": "--- a/main.py\n+++ b/main.py\n@@ -1,3 +1,4 @@\n+import logging\n def main():\n     pass"
  }
}

# Tool registry calls:
patch_plan = preview_patch(
    diff="--- a/main.py\n+++ b/main.py\n...",
    project_root=Path("/workspace")
)

# Returns PatchPlan:
PatchPlan(
    file_path="main.py",
    diff="--- a/main.py\n+++ b/main.py\n...",
    rationale="Add logging import",
    estimated_lines_changed=1
)

# Graph pauses, UI shows patch preview modal
# User approves → execute_patch_approved() is called
# User denies → ToolOutput with error returned
```

**Implementation:** `src/tools/patching.py`

**Approval flow:**
1. Master Agent calls `apply_patch`
2. Tool execution node calls `preview_patch()`
3. Graph interrupts with approval request
4. UI shows patch preview modal
5. User approves/denies
6. If approved: `execute_patch_approved()` applies the patch
7. Modified file auto-opens in editor

#### 1.3 `search_workspace`
**Purpose:** Semantic search over workspace files via RAG

**Function signature:**
```python
def search_workspace(
    query: str,
    project_root: Path,
    k: int = 5  # Number of results
) -> List[Dict[str, Any]]
```

**Example invocation:**
```python
# LLM requests:
{
  "tool": "search_workspace",
  "args": {
    "query": "timer logic",
    "k": 5
  }
}

# Tool registry calls:
results = search_workspace(
    query="timer logic",
    project_root=Path("/workspace"),
    k=5
)

# Returns:
[
    {
        "file_path": "conveyor.st",
        "content": "T_ConveyorDelay : TON;  (* 5s delay *)\n...",
        "score": 0.92,
        "line_number": 15
    },
    ...
]
```

**Implementation:** `src/tools/rag.py`

---

### Tier 2: Permissioned Tools (Require Approval)

#### 2.1 `plan_terminal_cmd`
**Purpose:** Generate terminal command plan with risk assessment

**Function signature:**
```python
def plan_terminal_cmd(
    command: str,
    rationale: str,
    project_root: Path
) -> CommandPlan
```

**Example invocation:**
```python
# LLM requests:
{
  "tool": "plan_terminal_cmd",
  "args": {
    "command": "pip install pytest",
    "rationale": "Install testing framework for unit tests"
  }
}

# Tool registry calls:
command_plan = plan_terminal_cmd(
    command="pip install pytest",
    rationale="Install testing framework",
    project_root=Path("/workspace")
)

# Returns CommandPlan:
CommandPlan(
    command="pip install pytest",
    rationale="Install testing framework",
    risk_label="MEDIUM",  # Auto-assessed
    timeout=300
)

# Graph pauses, UI shows terminal approval modal with risk label
# User sees: "MEDIUM RISK: pip install pytest"
# User approves → run_terminal_cmd() executes
# User denies → ToolOutput with error returned
```

**Implementation:** `src/tools/terminal.py`

**Risk assessment logic:**
- **HIGH:** `rm -rf`, `DROP TABLE`, `git reset --hard`, `format`
- **MEDIUM:** `pip install`, `npm install`, `git push`, `docker run`
- **LOW:** `ls`, `cat`, `git status`, `echo`, `pwd`

#### 2.2 `dependency_manager`
**Purpose:** Detect project dependencies and propose installation commands

**Function signature:**
```python
def dependency_manager(
    project_root: Path
) -> Dict[str, Any]
```

**Example invocation:**
```python
# LLM requests:
{
  "tool": "dependency_manager",
  "args": {}
}

# Tool registry calls:
result = dependency_manager(
    project_root=Path("/workspace")
)

# Returns:
{
    "detected": {
        "python": {
            "venv": True,
            "requirements_txt": True,
            "missing_packages": ["pytest", "black"]
        },
        "node": {
            "package_json": True,
            "node_modules": False
        }
    },
    "proposed_commands": [
        {
            "command": "pip install -r requirements.txt",
            "rationale": "Install Python dependencies",
            "risk_label": "MEDIUM"
        },
        {
            "command": "npm install",
            "rationale": "Install Node.js dependencies",
            "risk_label": "MEDIUM"
        }
    ]
}
```

**Implementation:** `src/tools/deps.py`

---

### Tier 3: Intelligence Tools (Web + Subsystems)

#### 3.1 `web_search`
**Purpose:** Search the web for documentation and technical resources

**Function signature:**
```python
def web_search(
    query: str,
    num_results: int = 5
) -> List[Dict[str, Any]]
```

**Example invocation:**
```python
# LLM requests:
{
  "tool": "web_search",
  "args": {
    "query": "Flet ExpansionTile documentation",
    "num_results": 5
  }
}

# Tool registry calls:
results = web_search(
    query="Flet ExpansionTile documentation",
    num_results=5
)

# Returns:
[
    {
        "title": "ExpansionTile - Flet",
        "url": "https://flet.dev/docs/controls/expansiontile",
        "snippet": "ExpansionTile is a control that expands and collapses..."
    },
    ...
]
```

**Implementation:** `src/tools/web_search.py` (DuckDuckGo API)

**When to use:**
- Workspace search returns no results
- User asks about external libraries/frameworks
- Documentation lookup needed
- Stack Overflow answers needed

---

#### 3.2 `implement_feature` (CrewAI Subsystem)
**Purpose:** Delegate complex feature implementation to specialized agents

**Function signature:**
```python
async def implement_feature(
    request: str,
    project_root: Path,
    context: Optional[str] = None
) -> Dict[str, Any]
```

**Example invocation:**
```python
# LLM requests:
{
  "tool": "implement_feature",
  "args": {
    "request": "Add user authentication with JWT tokens",
    "context": "Using FastAPI framework"
  }
}

# Tool registry calls (async):
result = await implement_feature(
    request="Add user authentication with JWT tokens",
    project_root=Path("/workspace"),
    context="Using FastAPI framework"
)

# CrewAI workflow (runs in background thread):
#   1. Planner Agent analyzes request → generates plan
#   2. Coder Agent writes code based on plan
#   3. Reviewer Agent reviews for quality/safety

# Returns FeatureResult:
{
    "patch_plans": [
        {
            "file_path": "auth.py",
            "diff": "--- a/auth.py\n+++ b/auth.py\n...",
            "rationale": "Add JWT authentication middleware"
        },
        {
            "file_path": "models.py",
            "diff": "--- a/models.py\n+++ b/models.py\n...",
            "rationale": "Add User model"
        }
    ],
    "summary": "Implemented JWT authentication with FastAPI",
    "verification_steps": [
        "1. Run: pytest tests/test_auth.py",
        "2. Test login endpoint: POST /api/login",
        "3. Verify token validation"
    ],
    "metadata": {
        "planner_iterations": 1,
        "coder_iterations": 3,
        "reviewer_approval": "YES",
        "risk_level": "MEDIUM"
    }
}

# Master Agent receives ONLY this structured output
# CrewAI agent transcripts are DISCARDED (not in context)
```

**Implementation:** `src/tools/builder_crew.py`

**Key Concepts:**

1. **Context Containment:**
   - CrewAI agents debate and collaborate internally
   - ONLY structured output (PatchPlan list) returns to Master
   - Transcripts never pollute Master Agent context

2. **Background Execution:**
   ```python
   # Tool registry wraps the call:
   result = await asyncio.to_thread(crew.kickoff)
   ```
   - Prevents UI freeze during long-running crew work
   - User sees "vibe status" updates (e.g., "Preparing")

3. **When to Use:**
   - User request is complex (>3 files affected)
   - Requires architectural planning
   - Benefits from multi-agent collaboration
   - Examples:
     - "Add authentication system"
     - "Implement API rate limiting"
     - "Create admin dashboard"
     - "Add conveyor control logic with safety interlocks"

4. **When NOT to Use:**
   - Simple file creation
   - Single-line edits
   - Direct answers to questions
   - Examples:
     - "create test.txt" ❌ Use manage_file_ops
     - "fix typo in line 42" ❌ Use apply_patch directly

---

#### 3.3 `diagnose_project` (AutoGen Subsystem)
**Purpose:** Run project health audit with deterministic + AI debate

**Function signature:**
```python
async def diagnose_project(
    focus_area: Optional[str] = None,
    project_root: Path,
    context: Optional[str] = None
) -> Dict[str, Any]
```

**Example invocation:**
```python
# LLM requests:
{
  "tool": "diagnose_project",
  "args": {
    "focus_area": "syntax errors"
  }
}

# Tool registry calls (async):
result = await diagnose_project(
    focus_area="syntax errors",
    project_root=Path("/workspace"),
    context=None
)

# AutoGen workflow (runs in background thread):
#   1. Deterministic checks (file structure, imports, syntax)
#   2. AutoGen debate (finds subtle issues via multi-agent discussion)

# Returns DiagnosisResult:
{
    "risk_level": "HIGH",
    "findings": [
        {
            "severity": "ERROR",
            "file": "main.py",
            "line": 42,
            "message": "Undefined variable 'user_id'"
        },
        {
            "severity": "WARNING",
            "file": "utils.py",
            "line": 15,
            "message": "Function 'calculate_total' has no docstring"
        }
    ],
    "prioritized_fixes": [
        {
            "priority": 1,
            "action": "Define 'user_id' or remove reference",
            "rationale": "Undefined variable will cause runtime error"
        },
        {
            "priority": 2,
            "action": "Add docstring to calculate_total",
            "rationale": "Improves code maintainability"
        }
    ],
    "verification_steps": [
        "1. Run: python -m py_compile main.py",
        "2. Run: pytest tests/"
    ],
    "metadata": {
        "deterministic_checks": 15,
        "autogen_findings": 3,
        "debate_rounds": 2
    }
}

# Master Agent receives ONLY this JSON output
# AutoGen debate transcripts are DISCARDED
```

**Implementation:** `src/tools/auditor_swarm.py`

**Key Concepts:**

1. **Hybrid Approach:**
   - Deterministic checks run first (fast, cheap)
   - AutoGen debate optional (slower, finds subtle issues)

2. **When to Use:**
   - User asks: "check project for errors"
   - Before major refactoring
   - After merging code
   - Debugging mysterious issues

3. **Output Format:**
   - Strict JSON schema (defined in AUTOGEN_AUDITOR_PROMPT)
   - Findings sorted by severity (ERROR > WARNING > INFO)
   - Fixes prioritized (1 = most critical)

---

## Complete Flow Example: "create test.txt"

**Step-by-step execution:**

1. **User Input:**
   ```
   User types in Pulse Chat: "create test.txt"
   ```

2. **Master Agent Node:**
   ```python
   # src/agents/master_graph.py:143

   # Load system prompt
   system_prompt = AGENT_MODE_PROMPT  # General-purpose prompt

   # No .st files, so no PLC enhancement

   # Get tool schemas
   tool_schemas = registry.get_tool_schemas(mode="agent")
   # Returns: [manage_file_ops, apply_patch, search_workspace, ...]

   # Call LLM
   llm_response = llm_client.generate(
       model="gpt-4o",
       messages=[{"role": "user", "content": "create test.txt"}],
       system_prompt=system_prompt,
       tools=tool_schemas
   )
   ```

3. **LLM Response:**
   ```json
   {
     "tool_calls": [
       {
         "id": "call_abc123",
         "name": "manage_file_ops",
         "arguments": {
           "operation": "create",
           "path": "test.txt",
           "content": ""
         }
       }
     ]
   }
   ```

4. **Tool Execution Node:**
   ```python
   # src/agents/master_graph.py:348

   tool_name = "manage_file_ops"
   tool_args = {"operation": "create", "path": "test.txt", "content": ""}

   # Check approval requirement
   requires_approval = tool_name in ["apply_patch", "plan_terminal_cmd"]
   # False for manage_file_ops

   # Execute tool
   tool_output = await execute_tool_real(tool_name, tool_args, state)
   ```

5. **Tool Registry:**
   ```python
   # src/tools/registry.py:233

   def invoke_tool(tool_name, args):
       tool = self.tools[tool_name]
       result = tool.function(args)  # Calls _wrap_file_ops
   ```

6. **File Ops Tool:**
   ```python
   # src/tools/file_ops.py

   def manage_file_ops(operation, path, project_root, content):
       file_path = project_root / path

       # Create file
       file_path.write_text(content or "")

       return {
           "status": "success",
           "path": str(path),
           "message": "File created successfully"
       }
   ```

7. **Result Returned:**
   ```python
   # Back to master_graph.py:566

   state["tool_result"] = ToolOutput(
       tool_name="manage_file_ops",
       success=True,
       result={"status": "success", "path": "test.txt", ...}
   )

   # Loop back to Master Agent
   ```

8. **Master Agent Final Response:**
   ```python
   # Master Agent sees successful tool execution
   # Provides confirmation to user

   state["agent_response"] = "Created test.txt successfully."
   ```

9. **UI Update:**
   - Pulse Chat shows: "Created test.txt successfully."
   - File tree sidebar refreshes
   - test.txt appears in workspace

**Total time: ~2 seconds**

---

## Debugging Tool Invocations

### Check if tool is registered:
```python
from src.agents.master_graph import get_tool_registry

registry = get_tool_registry()
tools = registry.list_tools()
print(tools)
```

### Verify tool schemas:
```python
schemas = registry.get_tool_schemas(mode="agent")
for schema in schemas:
    print(schema["function"]["name"])
```

### Test tool directly:
```python
from pathlib import Path

result = registry.invoke_tool(
    tool_name="manage_file_ops",
    args={
        "operation": "create",
        "path": "test.txt",
        "content": "Hello"
    }
)
print(result)
```

---

## Common Issues & Solutions

### Issue: Tool not found
**Symptom:** LLM doesn't call the tool, or "Tool not found" error
**Cause:** Tool not registered in `create_master_graph()`
**Solution:** Add `_tool_registry.register_tierX_tools()` call

### Issue: LLM doesn't use tools
**Symptom:** LLM provides direct answer instead of calling tools
**Cause:** Prompt doesn't emphasize tool usage
**Solution:** Update system prompt to include tool examples

### Issue: Approval modal doesn't appear
**Symptom:** Patch/command executes without user approval
**Cause:** Tool not marked as `requires_approval=True`
**Solution:** Check tool definition in `registry.py`

### Issue: CrewAI/AutoGen takes too long
**Symptom:** UI freezes during subsystem execution
**Cause:** Not using `asyncio.to_thread()`
**Solution:** Ensure wrapper uses `await asyncio.to_thread(crew.kickoff)`

---

## Summary

**Tool Invocation Flow:**
```
User Input
    ↓
Master Agent (LLM decides tool)
    ↓
Tool Execution Node (approval check)
    ↓
Tool Registry (invoke tool)
    ↓
Tool Implementation (file_ops, patching, etc.)
    ↓
Result → Master Agent
    ↓
User Response
```

**Key Principles:**
1. **Master Agent is the brain** - makes all decisions via LLM function calling
2. **Tools are the hands** - execute specific actions
3. **Approval gates** protect user from unintended changes
4. **Context containment** keeps subsystem complexity out of Master context
5. **Background execution** prevents UI freezing

**When in doubt:**
- Simple tasks → Tier 1 tools (manage_file_ops)
- Risky operations → Tier 2 tools (plan_terminal_cmd)
- Complex features → Tier 3 tools (implement_feature, diagnose_project)
