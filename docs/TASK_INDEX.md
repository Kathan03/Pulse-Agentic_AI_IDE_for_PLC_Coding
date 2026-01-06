# Pulse IDE - Implementation Task Index

**Purpose:** Detailed task instructions for Claude Code sessions. Each task is self-contained with enough context for correct implementation.

**Usage:** Start a new Claude Code session and say: `"Implement Task [ID] from docs/TASK_INDEX.md"`

---

## A1: Process ALL Tool Calls Per Iteration

**File:** `src/agents/master_graph.py`

**Problem:** Currently processes only the FIRST tool call when LLM returns multiple. This causes unnecessary LLM round-trips.

**Current code (around line 258-290):**
```python
if llm_response.tool_calls:
    tool_call = llm_response.tool_calls[0]  # Only first!
    # ... stores single tool in state["tool_result"]
```

**Required change:**
1. In `master_agent_node`: Store ALL tool calls in state, not just first
2. In `tool_execution_node`: Loop through and execute ALL tool calls
3. Add all tool results to message history before returning to master_agent

**New behavior:**
- If LLM returns `[read_file, read_file, grep]`, execute all 3 before next LLM call
- Add each tool result to `state["messages"]` in function-calling format
- Only tools requiring approval should pause (others execute immediately)

**State changes needed:**
- Change `state["tool_result"]` from single `ToolOutput` to `List[ToolOutput]`
- Or add new field `state["pending_tool_calls"]: List[Dict]`

**Test:** Ask agent to "read main.py and requirements.txt" - should see 2 tool calls execute before response.

---

## A2: Improve Prompts with ReAct + CoT Patterns

**File:** `src/core/prompts.py`

**Problem:** Current prompts are basic role descriptions. Need explicit reasoning patterns.

**Changes to AGENT_MODE_PROMPT:**

Add at the beginning:
```
Before taking any action, think through your approach:
1. What is the user asking for?
2. What information do I need?
3. Which tools should I use and in what order?
4. What could go wrong?

When you need to reason, use this format:
<thinking>
[Your step-by-step reasoning here]
</thinking>

Then proceed with tool calls or response.
```

Add tool selection guidance:
```
TOOL SELECTION GUIDE:
- To understand a codebase: Use manage_file_ops(list) first, then read specific files
- To find code: Use search_workspace for semantic search
- To modify code: Generate patch with apply_patch (user will approve)
- For terminal commands: Use plan_terminal_cmd with risk assessment
- When unsure about syntax/APIs: Use web_search first
```

Add error handling:
```
IF A TOOL FAILS:
1. Read the error message carefully
2. Identify the root cause (wrong path? missing file? permission?)
3. Try an alternative approach
4. If stuck after 2 attempts, explain the issue to the user
```

**Apply similar patterns to ASK_MODE_PROMPT and PLAN_MODE_PROMPT.**

**Test:** Agent should show reasoning before tool calls and handle errors gracefully.

---

## A3: Enhance Memory Management

**Files:** `src/agents/state.py`, `src/agents/master_graph.py`

**Problem:** Current truncation just concatenates old messages as text. Loses important context.

**Changes:**

1. **In state.py** - Add new field:
```python
class MasterState(TypedDict):
    # ... existing fields ...
    conversation_summary: str  # LLM-generated summary of older messages
    important_context: List[str]  # Key facts to always preserve
```

2. **In master_graph.py** - Replace simple truncation with LLM summarization:
```python
async def summarize_old_messages(messages: List[Dict], llm_client) -> str:
    """Use LLM to create intelligent summary of old messages."""
    summary_prompt = """Summarize this conversation history in 2-3 sentences.
    Focus on: user's goal, files discussed, decisions made, current progress."""

    response = llm_client.generate(
        model="gpt-4o-mini",  # Use cheap model for summarization
        messages=[{"role": "user", "content": f"Summarize:\n{format_messages(messages)}"}],
        system_prompt=summary_prompt
    )
    return response.content
```

3. **Preserve key context:**
- Files touched in this session
- User's original request
- Any errors encountered
- Decisions made (approved patches, etc.)

**Test:** Have a long conversation (15+ exchanges), verify agent remembers early context.

---

## B1: Delete Unused Files

**Action:** Delete these files if they exist:
- `src/ui/components/code_preview_panel.py` (duplicate of approval.py)
- `src/ui/components/loading_animation.py` (unused)
- `src/ui/components/clarification_dialog.py` (not used in v2.6)

**Verification:** Run `python -c "from src.ui.components import *"` - should not error.

---

## B2: Update Component Exports

**File:** `src/ui/components/__init__.py`

**Action:** After B1, ensure __init__.py only exports existing files. Current exports look correct, but verify no broken imports after deletion.

---

## C1: Create Granular Prompt Configuration

**File:** `src/core/prompts.py`

**Goal:** Modular prompt system for dynamic composition.

**Structure:**
```python
# Base components (always included)
BASE_IDENTITY = """You are Pulse, an AI assistant for PLC programming..."""
BASE_SAFETY = """Never execute destructive commands without approval..."""
BASE_TOOLS = """You have access to these tools: {tool_list}"""

# Mode-specific
MODE_AGENT = """You can read, write, and execute. Be decisive..."""
MODE_ASK = """You can only read and search. Do not modify..."""
MODE_PLAN = """Create a detailed plan without executing..."""

# Task-specific (added dynamically based on user request)
TASK_EXPLORE = """When exploring a codebase: Start with file listing..."""
TASK_DEBUG = """When debugging: Reproduce the issue first..."""
TASK_REFACTOR = """When refactoring: Preserve behavior..."""

# Composition function
def build_system_prompt(mode: str, tasks: List[str] = None) -> str:
    prompt = BASE_IDENTITY + "\n\n" + BASE_SAFETY + "\n\n"

    if mode == "agent":
        prompt += MODE_AGENT
    elif mode == "ask":
        prompt += MODE_ASK
    else:
        prompt += MODE_PLAN

    if tasks:
        for task in tasks:
            prompt += "\n\n" + TASK_PROMPTS.get(task, "")

    return prompt
```

**Usage in master_graph.py:**
```python
system_prompt = build_system_prompt(
    mode=state["mode"],
    tasks=detect_task_type(state["user_input"])  # "explore", "debug", etc.
)
```

---

## C2: Add Task-Specific Prompts

**File:** `src/core/prompts.py`

**Add these prompt components:**

```python
TASK_EXPLORE = """
EXPLORATION MODE:
1. Start with manage_file_ops(action="list") to see structure
2. Identify key directories (src/, tests/, config/)
3. Read README.md or similar docs first
4. Use search_workspace for specific queries
5. Build mental model before diving into code
"""

TASK_DEBUG = """
DEBUGGING MODE:
1. Reproduce: Understand exactly when the bug occurs
2. Isolate: Find the minimal case that triggers it
3. Locate: Search for relevant code with search_workspace
4. Analyze: Read the code, trace the logic
5. Fix: Generate minimal patch to fix the issue
6. Verify: Suggest how to test the fix
"""

TASK_REFACTOR = """
REFACTORING MODE:
1. Understand: Read all affected code first
2. Preserve: Behavior must not change
3. Incremental: Small changes, test between each
4. Document: Explain why each change improves the code
"""

TASK_TEST = """
TEST GENERATION MODE:
1. Analyze: Read the code to understand behavior
2. Identify: Edge cases, error conditions, happy paths
3. Structure: Use existing test patterns in the codebase
4. Cover: Aim for meaningful coverage, not just lines
"""

TASK_REVIEW = """
CODE REVIEW MODE:
1. Security: Check for vulnerabilities (injection, auth, etc.)
2. Performance: Identify bottlenecks or inefficiencies
3. Maintainability: Is the code readable? Well-structured?
4. Correctness: Does it do what it claims?
5. Format: Provide specific, actionable feedback
"""
```

---

## C3: Improve PLC-Specific Prompts

**File:** `src/core/prompts.py`

**Enhance PLC_ENHANCEMENT with:**

```python
PLC_ENHANCEMENT = """
## IEC 61131-3 Structured Text Expertise

### Timer/Counter Patterns
- TON: On-delay timer. Use for "wait X seconds before action"
- TOF: Off-delay timer. Use for "keep active X seconds after trigger"
- TP: Pulse timer. Use for "activate for exactly X seconds"
- CTU/CTD: Count up/down. Use for batch counting, sequences

### Safety-Critical Patterns (ALWAYS FOLLOW)
1. E-Stop Logic: E-Stop must be hardwired, software is backup only
2. Watchdog: Always implement software watchdog for critical loops
3. Interlocks: Motors must have mechanical interlock verification
4. State Machines: Use explicit states, never implicit conditions
5. Fail-Safe: Default state must be safe (motors off, valves closed)

### Common Patterns
```st
// Debounce a digital input
IF Input AND NOT Input_Prev THEN
    Debounce_Timer(IN:=TRUE, PT:=T#50ms);
END_IF;
IF Debounce_Timer.Q THEN
    Stable_Input := TRUE;
END_IF;

// Motor start/stop with interlock
Motor_Run := Start_Cmd AND NOT Stop_Cmd AND NOT E_Stop AND Interlock_OK;
```

### Naming Conventions
- Inputs: I_SensorName (e.g., I_ProxSensor1)
- Outputs: O_ActuatorName (e.g., O_Motor1)
- Timers: T_Description (e.g., T_StartupDelay)
- States: ST_MachineName_State (e.g., ST_Conveyor_Running)
"""
```

---

## D1: Integrate Monaco Editor (Main Editor)

**File:** `src/ui/editor.py`

**This is a major change. High-level approach:**

1. **Create Monaco wrapper component** using Flet's WebView or HTML component
2. **Remove:** `PythonHighlighter`, `SyntaxColors` classes
3. **Keep:** `EditorManager` class, tab management, file open/close logic
4. **Add:** Python ↔ Monaco bridge for:
   - Setting content: `monaco.setValue(content)`
   - Getting content: `monaco.getValue()`
   - Dirty detection: `monaco.onDidChangeModelContent`
   - Theme sync: `monaco.editor.setTheme`

**Monaco HTML template:**
```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs/loader.js"></script>
</head>
<body>
    <div id="editor" style="width:100%;height:100%"></div>
    <script>
        require.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs' } });
        require(['vs/editor/editor.main'], function () {
            window.editor = monaco.editor.create(document.getElementById('editor'), {
                theme: 'vs-dark',
                language: 'python',
                automaticLayout: true
            });

            // Bridge to Python
            window.editor.onDidChangeModelContent(() => {
                window.postMessage({ type: 'content_changed' });
            });
        });

        function setContent(content) { window.editor.setValue(content); }
        function getContent() { return window.editor.getValue(); }
    </script>
</body>
</html>
```

**Note:** This task requires research on Flet WebView communication patterns.

---

## D2: Integrate Monaco Diff View

**File:** `src/ui/components/approval.py`

**Change:** Replace text-based diff in `PatchApprovalModal` with Monaco diff editor.

**Monaco diff setup:**
```javascript
var diffEditor = monaco.editor.createDiffEditor(container, {
    theme: 'vs-dark',
    readOnly: true,
    renderSideBySide: true
});

diffEditor.setModel({
    original: monaco.editor.createModel(originalContent, 'python'),
    modified: monaco.editor.createModel(modifiedContent, 'python')
});
```

**Keep:** Approve/Deny buttons, rationale display, feedback field
**Remove:** Manual diff line coloring code (lines 63-105)

---

## D3: Fix Sidebar Scrolling

**File:** `src/ui/sidebar.py`

**Problem:** Sidebar doesn't scroll when file list is long.

**Fix:** Find the main Column or Container and add `scroll=ft.ScrollMode.AUTO` and `expand=True`.

**Pattern:**
```python
ft.Column(
    controls=[...],
    scroll=ft.ScrollMode.AUTO,  # Add this
    expand=True,  # Add this
)
```

---

## D4: Improve File Tree (VS Code-style)

**File:** `src/ui/sidebar.py`

**Goal:** Expandable/collapsible folders using Flet's ExpansionTile.

**Pattern:**
```python
def build_file_tree(path: Path) -> ft.Control:
    if path.is_dir():
        children = [build_file_tree(child) for child in sorted(path.iterdir())]
        return ft.ExpansionTile(
            title=ft.Text(path.name),
            leading=ft.Icon(ft.Icons.FOLDER),
            controls=children,
            initially_expanded=False,
        )
    else:
        return ft.ListTile(
            title=ft.Text(path.name),
            leading=ft.Icon(get_file_icon(path.suffix)),
            on_click=lambda e: open_file(path),
        )
```

---

## E1: Add Parallel Tool Execution

**File:** `src/agents/master_graph.py`

**Context:** Code exists (lines ~370-460) but not integrated.

**Enable parallel execution for:**
- Multiple `manage_file_ops(action="read")` calls
- Multiple `search_workspace` calls
- Any combination of read-only tools

**Keep sequential for:**
- Any tool requiring approval (`apply_patch`, `plan_terminal_cmd`)
- Tools with dependencies (read → modify → read)

**Implementation:**
```python
async def execute_tools_parallel(tool_calls, state):
    # Separate into parallel-safe and sequential
    parallel_safe = [tc for tc in tool_calls if is_read_only(tc)]
    sequential = [tc for tc in tool_calls if not is_read_only(tc)]

    # Execute parallel batch
    if parallel_safe:
        results = await asyncio.gather(*[
            execute_single_tool(tc, state) for tc in parallel_safe
        ])
        for result in results:
            append_to_history(result)

    # Execute sequential
    for tc in sequential:
        result = await execute_single_tool(tc, state)
        append_to_history(result)
        if result.requires_approval:
            return  # Pause for approval
```

---

## E2: Improve Tool Output Formatting

**File:** `src/tools/registry.py`

**Goal:** Standardize output for LLM consumption.

**Current:** Tool outputs are raw dicts/strings.

**New format:**
```python
class ToolOutput:
    success: bool
    result: Any
    error: Optional[str]
    summary: str  # NEW: Human-readable 1-line summary
    next_steps: List[str]  # NEW: Suggested follow-up actions

# Example output:
ToolOutput(
    success=True,
    result={"content": "...", "lines": 150},
    summary="Read main.py (150 lines)",
    next_steps=["Search for specific function", "Read imported modules"]
)
```

**Helps LLM:** Understand tool results quickly without parsing raw data.

---

## E3: Add Tool Usage Analytics (Optional)

**New file:** `src/core/analytics.py`

**Purpose:** Track which tools are used, success rates, common patterns.

**Simple implementation:**
```python
import json
from pathlib import Path
from datetime import datetime

ANALYTICS_FILE = ".pulse/analytics.json"

def log_tool_usage(tool_name: str, success: bool, duration_ms: int):
    data = load_analytics()
    data["tool_calls"].append({
        "tool": tool_name,
        "success": success,
        "duration_ms": duration_ms,
        "timestamp": datetime.now().isoformat()
    })
    save_analytics(data)
```

**Use for:** Identifying slow tools, common failure patterns, prompt optimization.

---

## F1: Persist Conversation History

**Files:** `src/core/db.py`, `src/agents/runtime.py`

**Goal:** Save conversations to SQLite for resume and export.

**Schema:**
```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    project_root TEXT,
    title TEXT
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    conversation_id TEXT,
    role TEXT,  -- user, assistant, tool
    content TEXT,
    tool_calls TEXT,  -- JSON
    created_at TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);
```

**In runtime.py:**
```python
async def run_agent(...):
    conversation_id = create_or_resume_conversation(project_root)
    # ... after each message exchange ...
    save_message(conversation_id, role, content, tool_calls)
```

---

## F2: Improve Vibe Status Updates

**Files:** `src/agents/master_graph.py`, `src/ui/bridge.py`

**Add more granular updates:**
```python
# In tool_execution_node:
await emit_status("Reading files...")  # Before file reads
await emit_status("Searching codebase...")  # Before search
await emit_status("Generating patch...")  # Before patch creation
await emit_status("Waiting for approval...")  # During approval
```

**Add progress for long operations:**
```python
# For multi-file reads:
for i, file in enumerate(files):
    await emit_status(f"Reading file {i+1}/{len(files)}...")
    content = read_file(file)
```

---

## G1: Add Error Recovery Patterns

**File:** `src/agents/master_graph.py`

**Add retry logic:**
```python
async def call_llm_with_retry(llm_client, messages, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await llm_client.generate(...)
        except RateLimitError:
            wait = 2 ** attempt  # Exponential backoff
            await asyncio.sleep(wait)
        except APIError as e:
            if attempt == max_retries - 1:
                return create_error_response(f"API error after {max_retries} attempts: {e}")
            await asyncio.sleep(1)
```

**User-friendly errors:**
```python
ERROR_MESSAGES = {
    "rate_limit": "API rate limit reached. Please wait a moment.",
    "api_key_invalid": "API key is invalid. Check Settings > API Keys.",
    "network": "Network error. Check your internet connection.",
}
```

---

## G2: Add Cost/Token Tracking

**File:** `src/core/llm_client.py`

**Track in LLMResponse:**
```python
@dataclass
class LLMResponse:
    content: str
    tool_calls: List[ToolCall]
    usage: TokenUsage  # NEW

@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float  # Based on model pricing
```

**Accumulate per session:**
```python
class SessionCostTracker:
    total_tokens: int = 0
    total_cost_usd: float = 0.0

    def add(self, usage: TokenUsage):
        self.total_tokens += usage.total_tokens
        self.total_cost_usd += usage.estimated_cost_usd
```

---

## G3: Improve Cancellation Handling

**Files:** `src/agents/runtime.py`, `src/agents/master_graph.py`

**Faster cancellation:**
```python
# Check cancellation more frequently
async def master_agent_node(state):
    if state["is_cancelled"]:
        return {"agent_response": "Cancelled by user."}

    # Check before each major operation
    for tool_call in tool_calls:
        if state["is_cancelled"]:
            return {"agent_response": f"Cancelled. Completed {completed} of {total} tools."}
        await execute_tool(tool_call)
```

**Clean state on cancel:**
```python
def cancel_run():
    state["is_cancelled"] = True
    state["pending_approval"] = None
    state["tool_result"] = None
    # Emit cancellation event
    emit_event(EventType.RUN_CANCELLED, {"partial_result": state.get("agent_response", "")})
```

---

## Implementation Order

| Priority | Task | Effort | Dependencies |
|----------|------|--------|--------------|
| 1 | A1 | Medium | None |
| 2 | B1 | Low | None |
| 3 | B2 | Low | B1 |
| 4 | A2 | High | None |
| 5 | C1 | Medium | A2 |
| 6 | C2 | Medium | C1 |
| 7 | D3 | Low | None |
| 8 | A3 | High | A1 |
| 9 | E1 | Medium | A1 |
| 10 | D1 | High | None |
| 11 | D2 | Medium | D1 |
| 12 | F1 | Medium | None |
| 13 | C3 | Medium | C1 |
| 14 | D4 | Medium | D3 |
| 15 | E2 | Low | A1 |
| 16 | G1 | Medium | None |
| 17 | F2 | Low | None |
| 18 | G2 | Low | None |
| 19 | G3 | Low | None |
| 20 | E3 | Low | None |
