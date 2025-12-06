# Pulse - Agentic AI IDE for PLC Coding

## CORE CONSTRAINTS (Strict Adherence Required)


1. **Platform:** Windows Desktop Application (Local-first).
2. **UI Framework:** Python + Flet (No web frameworks like React/Vue).
3. **Orchestration:** LangGraph (multi-agent graph) + CrewAI/Autogen (node implementation).
4. **Persistence:** SQLite (State) + Local File System (Workspace).
5. **No Cloud:** All processing and storage are local (except LLM API calls).
6. **Timeline:** 7 days (~140 hours) to ship fully functional IDE.

## PROJECT SCOPE

We are building a **fully functional IDE** where an Automation Engineer can:
- Open a local folder (Workspace) with a professional file explorer
- View/Edit .st (Structured Text) files in a **VS Code-style tabbed editor**
- Use an **integrated terminal** at the bottom of the IDE
- **Resize all panels** (sidebar, editor, terminal) with draggable splitters
- Input natural language tasks via **Pulse Chat** (permanent first tab in editor)
- Select interaction mode (Agent/Plan/Ask) from **Mode Selector** in sidebar
- Watch agents (Planner → Coder → Tester → QA → Customizer) generate/edit code
- Open multiple files simultaneously in **separate tabs** with close buttons
- Review agent activity and provide feedback in **Agent Panel**

**Scope Philosophy:**
- **UI:** Fully functional IDE experience (VS Code-level UX)
- **Agents:** MVP implementation using OpenAI GPT-4o

## ARCHITECTURE

### Complete Directory Structure (Source of Truth)

```
Pulse/
│
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies (includes crewai, autogen)
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore patterns
├── README.md                        # Project documentation
│
├── src/                             # Source code root
│   ├── __init__.py
│   │
│   ├── ui/                          # Flet UI Components (Presentation Layer)
│   │   ├── __init__.py
│   │   ├── app.py                   # Main Flet application controller (VS Code layout)
│   │   ├── sidebar.py               # Mode selector + workspace file tree
│   │   ├── editor.py                # EditorManager: Tabbed editor with Pulse Chat
│   │   ├── terminal.py              # Integrated terminal panel (NEW)
│   │   ├── agent_panel.py           # Agent mode selector + customizer feedback (NEW)
│   │   ├── test_panel.py            # Validation results display
│   │   ├── feedback_prompt.py       # Rating and feedback collection UI
│   │   └── components/              # Reusable UI widgets
│   │       ├── __init__.py
│   │       ├── file_tree.py         # Workspace folder tree widget
│   │       ├── plan_view.py         # Plan steps display widget
│   │       └── resizable_splitter.py # Draggable splitters for resizing (NEW)
│   │
│   ├── agents/                      # LangGraph Agent Nodes (Orchestration Layer)
│   │   ├── __init__.py
│   │   ├── graph.py                 # LangGraph orchestration setup
│   │   ├── planner.py               # Planner Agent node (uses CrewAI/Autogen)
│   │   ├── coder.py                 # Coder Agent node (uses CrewAI mini-crew)
│   │   ├── tester.py                # Tester Agent node (uses CrewAI/Autogen)
│   │   ├── qa.py                    # QA Agent node (RAG-powered)
│   │   └── customizer.py            # Customizer Agent node (feedback)
│   │
│   ├── core/                        # Core Business Logic & Infrastructure
│   │   ├── __init__.py
│   │   ├── state.py                 # LangGraph state schema (Pydantic models)
│   │   ├── config.py                # Application configuration
│   │   ├── file_manager.py          # Workspace file I/O with atomic writes
│   │   ├── db.py                    # SQLite session persistence manager
│   │   ├── rag.py                   # Chroma vector store & RAG logic
│   │   ├── llm_client.py            # LLM provider abstraction (OpenAI GPT-4o)
│   │   └── crew_factory.py          # CrewAI/Autogen crew factory (NEW)
│   │
│   └── tools/                       # Utility Functions & Helper Tools
│       ├── __init__.py
│       ├── logger.py                # Structured logging utility
│       ├── validation.py            # Input validation helpers
│       └── atomic_writer.py         # Safe file write operations
│
├── data/                            # Local Persistence (gitignored)
│   ├── pulse.db                     # SQLite database for sessions/state
│   ├── chroma/                      # Chroma vector store directory
│   └── feedback/                    # JSONL feedback logs
│       └── feedback.jsonl           # Append-only feedback log
│
├── workspace/                       # User workspace (example/default)
│   └── .keep                        # Placeholder to preserve directory
│
├── tests/                           # Test Suite
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures
│   ├── test_agents/                 # Agent orchestration tests
│   │   ├── __init__.py
│   │   ├── test_planner.py
│   │   ├── test_coder.py
│   │   └── test_tester.py
│   ├── test_core/                   # Core functionality tests
│   │   ├── __init__.py
│   │   ├── test_file_manager.py
│   │   ├── test_db.py
│   │   └── test_rag.py
│   └── test_ui/                     # UI component tests
│       └── __init__.py
│
└── .github/                         # CI/CD Pipeline
    └── workflows/
        └── ci-cd.yml                # GitHub Actions workflow
```

### Directory Responsibilities

**Root Level:**
- `main.py` - Flet app entry point; initializes VS Code-style UI
- `requirements.txt` - All Python dependencies (flet, langgraph, crewai, autogen)
- `.env.example` - Template for API keys (OPENAI_API_KEY, etc.)

**`/src/ui` - Presentation Layer (VS Code-like IDE):**
- `app.py` - Main layout controller with resizable panes
- `editor.py` - **EditorManager** with tabbed interface:
  - Tab 0: **Pulse Chat** (permanent agent interface)
  - Dynamic tabs: File viewers with close buttons
  - Tab headers showing filename
- `terminal.py` - **Terminal Panel** (bottom pane, dark theme, monospace)
- `sidebar.py` - **Mode Selector** (Agent/Plan/Ask) + File Tree
- `agent_panel.py` - **Agent Panel** for mode selection and feedback
- `components/resizable_splitter.py` - **Draggable Splitters** for panel resizing

**`/src/agents` - Orchestration Layer (LangGraph + CrewAI/Autogen):**
- Each agent is a **LangGraph node**
- **Internal implementation** uses CrewAI/Autogen for sub-task decomposition
- Example: `coder.py` uses a CrewAI mini-crew to iterate on code generation
- `graph.py` defines the multi-agent workflow (Agent/Plan/Ask modes)

**`/src/core` - Business Logic & Infrastructure:**
- `state.py` - Single source of truth for LangGraph state schema
- `file_manager.py` - All workspace file operations (atomic writes)
- `db.py` - SQLite persistence for sessions
- `rag.py` - Chroma vector store + RAG query logic
- `llm_client.py` - Abstraction over LLM providers (OpenAI GPT-4o primary)
- `crew_factory.py` - **CrewAI/Autogen crew instantiation helper**

**`/src/tools` - Utilities:**
- Shared helper functions
- Logging, validation, atomic writes

**`/data` - Local Persistence (gitignored):**
- `pulse.db` - SQLite database
- `chroma/` - Vector store for RAG
- `feedback/feedback.jsonl` - User feedback logs

**`/workspace` - User's PLC Code:**
- Default workspace folder (user can select any folder)
- Contains `.st` files (Structured Text PLC code)

**`/tests` - Test Suite:**
- Unit tests for agents, core, and tools
- Pytest framework
- Critical for CI/CD pipeline

### Technology Stack

- **Language:** Python 3.x
- **UI:** Flet (Python-driven desktop UI, VS Code-style)
- **Editor:** Tabbed EditorManager with Pulse Chat integration
- **Terminal:** Integrated terminal panel (Flet components)
- **Orchestration:**
  - **LangGraph** - Multi-agent workflow and state management
  - **CrewAI/Autogen** - Implementation detail INSIDE LangGraph nodes
- **Agent Implementation Pattern:**
  - LangGraph node = high-level orchestration
  - CrewAI/Autogen crew = internal task decomposition within node
  - Example: `coder_node(state)` → spawns CrewAI mini-crew → returns updated state
- **LLM:** OpenAI GPT-4o (primary for MVP agents)
- **Persistence:**
  - SQLite for sessions and state
  - Chroma (local vector store) for RAG
  - JSONL files for feedback logs
- **Packaging:** PyInstaller or flet pack for Windows .exe
- **CI/CD:** GitHub Actions

### UI Architecture (VS Code-Style)

**Layout Structure:**
```
┌─────────────────────────────────────────────────────────┐
│ [Workspace: My PLC Project]          [Mode: Agent ▾]    │
├──────────┬──────────────────────────────────────────────┤
│          │ ┌────────────────────────────────────────┐   │
│          │ │ [Pulse Chat] [main.st ×] [util.st ×]   │   │
│ Sidebar  ││ ├────────────────────────────────────────┤   │
│          │││ │                                       │   │
│ ┌──────┐ │││ │  Editor Content (Code/Chat)           │   │
│ │Agent │ │││ │                                       │   │
│ │Plan  │ │││ │                                       │   │
│ │Ask   │ │││ │                                       │   │
│ └──────┘ │││ │                                       │   │
│          │││ │                                       │   │
│ Files:   │││ │                                       │   │
│ ├─main.st│││ │                                       │   │
│ ├─util.st│││ └───────────────────────────────────────┘   │
│ └─io.st  │││ ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄   │
│          │││ ┌────────────────────────────────────────┐   │
│          │││ │ Terminal                               │   │
│          │││ │ Pulse> npm install                     │   │
│          │││ │ Installing packages...                 │   │
│          │││ └────────────────────────────────────────┘   │
│          │└──────────────────────────────────────────┘   │
└──────────┴──────────────────────────────────────────────┘
```

**Resizable Panels:**
- **Vertical Splitter:** Between Sidebar and Main Content
- **Horizontal Splitter:** Between Editor and Terminal
- Users drag splitters to adjust panel sizes

**Tabbed Editor:**
- **Tab 0 (Permanent):** "Pulse Chat" - Agent interface, never closable
- **Dynamic Tabs:** Files opened from sidebar, with [filename ×] in tab header
- **Close Button:** × icon on each file tab
- **Active Tab Highlighting:** Visual indication of current tab

**Integrated Terminal:**
- Black background, monospace font (Courier New / Consolas)
- Prompt: `Pulse> `
- Command history and output display
- Mimics VS Code terminal experience

## AGENT DESCRIPTIONS

### Architecture Pattern: LangGraph + CrewAI/Autogen

**Pattern:**
```python
# LangGraph Node (High-level orchestration)
def coder_node(state: PulseState) -> PulseState:
    # Internal implementation uses CrewAI/Autogen
    crew = create_coder_crew(state.plan, state.workspace)
    result = crew.kickoff()

    # Update state with results
    state.files_modified = result.files
    state.code_changes = result.changes
    return state
```

**Why This Pattern:**
- **LangGraph:** Manages overall agent workflow, state transitions, conditional routing
- **CrewAI/Autogen:** Handles complex sub-tasks within individual nodes (iterative refinement, multi-step reasoning)
- **Separation of Concerns:** Workflow orchestration ≠ Task execution

### 1. Planner Agent (High-Context Task Planner)
**Purpose:** Turn user's request into concrete, step-by-step implementation plan.

**Inputs:**
- User request (natural language)
- Snapshot of relevant project files

**Outputs:**
- Ordered list of Plan Steps (e.g., Analyze code, Add routine, Wire logic, Document)

**Implementation:**
- LangGraph node manages state flow
- Optional: CrewAI crew for complex multi-file analysis

**Responsibilities:**
- Make assumptions explicit (e.g., timer resolution, input/output names)
- Surface potential risks ("This change may affect cycle time")

**UX:** Plan steps displayed in Agent Panel. In Plan Mode, steps require user approval.

### 2. Coder Agent (File I/O + Code Generation)
**Purpose:** Translate plan steps into PLC-style code and actual file changes.

**Inputs:**
- Approved Plan Steps
- Current workspace state

**Outputs:**
- Concrete file operations (Create/Modify files)

**Implementation:**
- LangGraph node orchestrates file operations
- **CrewAI mini-crew** iterates on code quality:
  - Agent 1: Generate initial code
  - Agent 2: Review for PLC best practices
  - Agent 3: Optimize and finalize

**Responsibilities:**
- Use simplified Structured Text dialect for MVP
- Ensure code is idempotent (re-runnable without corruption)
- Adhere to simple coding style

**Safety:** Atomic writes constrained to workspace.

**Integration:** Files created/modified automatically open in new tabs.

### 3. Tester Agent (Validation)
**Purpose:** Validate generated/modified code against stated requirements.

**Inputs:**
- User requirement
- Updated files

**Outputs:**
- Test summary (Basic static checks, Suggested test cases)

**Implementation:**
- LangGraph node runs validation pipeline
- Optional: Autogen for multi-step validation logic

**MVP Behavior:** Focus on static analysis and requirement coverage mapping. Optionally generate pseudo-tests.

**UX:** Results displayed in Test Panel.

### 4. QA Agent (Context-Aware Q&A via RAG)
**Purpose:** Answer user questions about the codebase and changes.

**Inputs:**
- User question
- Vector search over project files

**Outputs:**
- Explanations referencing specific files/lines

**Implementation:**
- LangGraph node handles RAG query
- Chroma vector store for semantic search

**Responsibilities:**
- Summarize logic in human-friendly language
- Highlight impact of recent changes

**UX:** Answers displayed in Pulse Chat tab.

### 5. Customizer Agent (Feedback Loop & Telemetry)
**Purpose:** Capture structured feedback and logs for future model improvement.

**Inputs:**
- Session metadata
- User rating (1-5 stars)
- Optional free-text feedback

**Outputs:**
- Append-only JSONL logs stored locally

**Example Log Structure:**
```json
{
  "session_id": "...",
  "user_request": "...",
  "plan": [...],
  "files_touched": ["main.st"],
  "tests_summary": {...},
  "rating": 4,
  "feedback": "Code worked but needed more comments."
}
```

**UX:** Feedback panel in Agent Panel (right sidebar).

**Value:** Built-in fine-tuning data loop without cloud backend.

## INTERACTION MODES

### Mode Selector (Sidebar)
**UI Component:** Dropdown or SegmentedButton at top of Sidebar
**Options:**
1. **Agent Mode** (Fully Autonomous)
2. **Plan Mode** (Human-in-the-Loop)
3. **Ask Mode** (Q&A Only)

### 1. Agent Mode (Fully Autonomous)
**Flow:** Planner → Coder → Tester → QA → Customizer

**User Experience:**
- User enters requirement in **Pulse Chat** tab and clicks "Run"
- Pulse generates plan (shown in Agent Panel)
- Edits files automatically (new tabs open for modified files)
- Runs validation (results in Test Panel)
- Summarizes what changed in Pulse Chat
- Prompts for feedback in Agent Panel

**Use Case:** Quick iteration when user trusts the system.

### 2. Plan Mode (Human-in-the-Loop)
**Flow:** Planner → **(User Approves Plan)** → Coder → Tester → QA → Customizer

**User Experience:**
- User enters requirement in **Pulse Chat** and selects **Plan Mode**
- Planner presents step-by-step plan in Agent Panel
- User can approve or edit plan
- Only after approval does Coder modify files

**Use Case:** Higher-stakes changes requiring explicit review.

### 3. Ask Mode (Q&A Only)
**Flow:** QA → Customizer

**User Experience:**
- User asks questions in **Pulse Chat**
- No file changes performed
- Answers appear in Pulse Chat with file references (clickable to open in tabs)

**Use Case:** Code comprehension, impact analysis, debugging support.

## VS CODE-STYLE EDITOR (Critical Feature)

**Purpose:** Make Pulse a professional, day-to-day IDE experience.

### Features

**1. Tabbed Interface:**
- **Permanent Tab 0:** "Pulse Chat" (Agent interface, never closable)
- **Dynamic File Tabs:** Open files from sidebar, each in separate tab
- **Tab Headers:** `[filename ×]` with close button
- **Active Tab Highlight:** Visual distinction for current tab
- **Tab Switching:** Click tab headers to switch between files/chat

**2. File Operations:**
- **Opening Files:** Click file in sidebar → Opens in new tab (or focuses if already open)
- **Closing Files:** Click × on tab header → Closes tab (not Pulse Chat)
- **Auto-Open:** Files modified by Coder Agent automatically open in tabs

**3. Editor Affordances:**
- Monospaced font (Courier New / Consolas)
- Line numbers
- Syntax highlighting (basic for Structured Text)
- Save on Ctrl+S
- Changes immediately persist to disk

**4. Agent-Aware Editing:**
- Coder Agent reads files via same File Manager
- Writes trigger tab refresh if file is open
- Manual edits are ground truth for next agent run

**5. Safety:**
- All edits constrained to workspace
- Atomic writes to avoid corruption

### Integrated Terminal

**Location:** Bottom panel (below editor tabs)
**Appearance:**
- Black background (#1E1E1E)
- Green/white text (terminal style)
- Monospace font

**Features:**
- Command prompt: `Pulse> `
- Command history (↑/↓ arrow keys)
- Output display (stdout/stderr)
- Clear command
- Integration with workspace (commands run in workspace directory)

**Use Cases:**
- Run build scripts
- Execute PLC compiler commands
- Check file status
- Git operations

### Resizable Panels

**Implementation:** Draggable splitters using `ft.GestureDetector`

**Splitters:**
1. **Vertical Splitter:** Between Sidebar and Main Content
   - Drag left/right to resize sidebar width
2. **Horizontal Splitter:** Between Editor and Terminal
   - Drag up/down to resize terminal height

**User Experience:**
- Hover over splitter → Cursor changes to resize indicator
- Drag splitter → Live resize of adjacent panels
- Release → Panels lock at new size
- Sizes persist across sessions (saved in SQLite)

## PRIORITIES

### MUST HAVE (7-Day Timeline):

**UI (Fully Functional IDE):**
1. ✅ VS Code-style tabbed editor with Pulse Chat
2. ✅ Integrated terminal panel
3. ✅ Resizable panels with draggable splitters
4. ✅ Mode selector in sidebar
5. ✅ Agent panel for feedback and mode display
6. ✅ File tree with click-to-open functionality
7. ✅ Tab close buttons and active tab highlighting

**Agents (MVP with OpenAI GPT-4o):**
1. All 5 agents working in orchestrated flow
2. LangGraph + CrewAI/Autogen integration pattern
3. All 3 interaction modes (Agent, Plan, Ask)

**Core:**
1. Local persistence (SQLite + filesystem)
2. RAG over workspace files (Chroma)
3. Feedback collection system
4. Atomic file writes

**DevOps:**
1. GitHub Actions CI/CD pipeline
2. Windows .exe build

### KEEP SIMPLE:
- No cloud backend
- No multi-project management
- No direct PLC hardware connection
- Single PLC dialect (Structured Text-like)
- MVP agent intelligence (production-quality UI, MVP AI)

## OPERATIONAL EXCELLENCE

### CI/CD Pipeline (GitHub Actions)
**Triggers:**
- **On every push/PR to main:** Run linting and unit tests
- **On tag (e.g., v0.1.0):** Run tests, Build .exe, Attach to GitHub Release

**Jobs:**
1. **lint_and_test (Ubuntu):** Static analysis (ruff), Unit tests (pytest)
2. **build_windows (Windows):** Build .exe via PyInstaller or flet pack
3. **release (Ubuntu):** Create GitHub Release with attached Windows artifact

## SUCCESS CRITERIA

A reviewer can:
1. Install Pulse from GitHub Release .exe
2. **Experience a fully functional IDE:**
   - Open workspace and browse files in sidebar
   - Select mode from mode selector
   - Open multiple files in tabs
   - Close tabs with × button
   - Resize sidebar and terminal by dragging splitters
   - Use integrated terminal for commands
   - Switch between Pulse Chat and file tabs
3. Complete one end-to-end flow in each mode:
   - **Agent Mode:** requirement in Pulse Chat → code change → new file tab opens → feedback
   - **Plan Mode:** requirement → plan review in Agent Panel → approve → code change
   - **Ask Mode:** ask question in Pulse Chat → receive explanation with file references
4. **Perception:** "This is a real, professional IDE with AI agents, not a prototype"

## DEVELOPMENT PRINCIPLES

1. **Professional UI, MVP Agents:** Invest in IDE UX, use simple GPT-4o agents
2. **Local-First:** All data stays on user's machine
3. **Safety:** Atomic writes, workspace constraints, no destructive operations
4. **Modularity:**
   - LangGraph for workflow orchestration
   - CrewAI/Autogen for node implementation details
   - Clean separation of UI, agents, core
5. **VS Code Philosophy:** Familiar, professional, keyboard-friendly

## REFERENCE DOCUMENTS

- Full PRD: `Pulse_Agentic_AI_IDE_PRD.MD`
- This file (`CLAUDE.md`) is the **source of truth** for all implementation decisions

## TIMELINE: 7 Days

**Day 1-2:** UI Scaffolding (Tabs, Terminal, Splitters)
**Day 3-4:** Agent Integration (LangGraph + CrewAI/Autogen pattern)
**Day 5-6:** Polish, Testing, Bug Fixes
**Day 7:** CI/CD, Packaging, Documentation
