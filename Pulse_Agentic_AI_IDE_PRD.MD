# Pulse – Agentic AI IDE for PLC Coding

**Document Type:** Product Requirements Document (PRD)
**Timeline:** 7 days (~140 hours)
**Platform:** Windows Desktop Application
**Scope:** Fully functional IDE (UI) + MVP agents (OpenAI GPT-4o)

---

## 1. Problem Statement

Programming PLCs (Programmable Logic Controllers) today is:

* **Manual:** Engineers hand-write ladder logic or structured text in vendor-specific IDEs.
* **Error-prone:** Small mistakes in timing, interlocks, or I/O mapping can lead to production downtime or safety incidents.
* **Slow to iterate:** Each change requires mentally simulating logic, redeploying, and often involving on-site testing.
* **Tooling-fragmented:** IDEs do not provide modern AI assistance (planning, refactoring, context-aware Q&A).

Automation engineers are under pressure to ship changes quickly while maintaining reliability. They lack an “AI pair programmer” tailored to PLC workflows.

---

## 2. Proposed Solution – Pulse (“Cursor for PLC”)

Pulse is an Agentic AI IDE for PLC-style code, delivered as a local Windows desktop app. It acts as a PLC-focused “Cursor/Copilot,” helping engineers:

* Turn natural language requirements into structured plans.
* Generate and edit PLC-style code safely in a workspace on their machine.
* Validate logic against requirements and basic checks.
* Capture feedback for continuous improvement.

**Key design principles:**
* **Local-first:** Project files and logs stay on the user’s machine by default.
* **Operational excellence:** Automated CI/CD pipeline builds a signed .exe from GitHub pushes.
* **Agentic workflow:** Planner, Coder, Tester, QA, and Customizer agents collaborate through a structured orchestration layer.

---

## 3. User Persona

**Primary Persona – Automation Engineer**

* **Role:** Automation / Controls Engineer (in manufacturing, logistics, or process industry).
* **Goals:**
    * Implement PLC logic changes faster with fewer defects.
    * Understand and safely modify existing PLC programs.
    * Experiment with “what-if” logic changes before deploying to the PLC.
* **Pain Points:**
    * Vendor IDEs lack high-level guidance and explanation.
    * Debugging timing or state issues is tedious.
    * Little reuse or codification of tribal knowledge.
* **Environment:**
    * Windows laptop/desktop on or near the shop floor.
    * Mix of online/offline connectivity.
    * Often restricted from uploading code to external cloud services.

*For the MVP, we assume a technically comfortable engineer who is open to using an AI assistant, but still wants control over code and changes.*

---

## 4. Scope – Fully Functional IDE with MVP Agents

### Philosophy
* **UI & IDE Experience:** Production-quality, VS Code-level user experience (fully functional IDE)
* **Agent Implementation:** MVP using OpenAI GPT-4o (functional but not optimized)

### In Scope
**Windows desktop application built with:**
* **UI:** Python + Flet (VS Code-style layout and interactions)
* **Orchestration:** LangGraph (multi-agent workflow) + CrewAI/Autogen (node implementation)
* **Storage:** Local file system access to a user-selected workspace folder
* **Persistence:** SQLite for session/state persistence
* **RAG:** Local vector store (Chroma) for context-aware Q&A over project files

**Agentic core:**
* Planner, Coder, Tester, QA, Customizer agents (MVP implementation using GPT-4o)

**Interaction modes:**
* Agent Mode (fully autonomous loop)
* Plan Mode (human-in-the-loop)
* Ask Mode (chat/Q&A only)

**VS Code-style IDE features:**
* **Tabbed Editor:**
  * Multiple file tabs with close buttons (×)
  * Permanent "Pulse Chat" tab (Tab 0) for agent interactions
  * Click files in sidebar to open in new tabs
* **Integrated Terminal:**
  * Bottom panel with terminal interface
  * Black background, monospace font
  * Command history support
* **Resizable Panels:**
  * Draggable vertical splitter (sidebar ↔ main content)
  * Draggable horizontal splitter (editor ↔ terminal)
* **Workspace File Tree:**
  * Left sidebar showing folder structure
  * Files open in editor on click
* **Agent Panel:**
  * Mode selector (Agent/Plan/Ask)
  * Customizer feedback section

**CI/CD (GitHub Actions workflow):**
* Run tests and linting
* Build Windows .exe artifact via PyInstaller or flet pack
* Attach binary to GitHub Release

### Out of Scope
* Direct connection to live PLC hardware
* Support for multiple PLC vendor IDEs or proprietary project formats
* Rich project management (multi-project dashboards, collaboration)
* Cloud backend, user accounts, or centralized logging
* Advanced editor features (IntelliSense, debugger, extensions)

---

## 5. Solution Overview

At a high level:

1.  The user opens Pulse and selects a workspace folder containing PLC-style code (or starting empty).
2.  They view and edit code directly in an embedded text editor, just like a lightweight PLC IDE.
3.  They provide a natural-language task, e.g., *“Create a routine that toggles Motor_1 every 10 seconds with a fault latch.”*
4.  Pulse orchestrates a set of AI agents (Planner → Coder → Tester → QA → Customizer) to:
    * Plan the work.
    * Generate/edit PLC-style code and update files in the workspace.
    * Validate and summarize changes.
    * Ask for and record user feedback.
5.  All code and logs are stored locally in the workspace and in Pulse’s local data directory.

---

## 6. User Personas & Key Use Cases

### Primary Use Cases

**Generate new PLC logic from a requirement**
* User describes behavior in plain language.
* Pulse produces a plan, code files, and a brief explanation.
* Generated code is opened in the embedded editor for inspection and further manual edits.

**Modify existing PLC logic**
* User opens an existing project folder and selects files from the workspace tree.
* They review and optionally hand-edit the code in the integrated editor.
* User describes a desired change in natural language.
* Pulse:
    * Analyzes the current code.
    * Proposes a plan (in Plan Mode) or directly edits files (in Agent Mode).
    * Updates the same files the user can continue editing manually in the editor.

**Understand and explain existing code**
* User asks *“What does this timer do?”* or *“How is Motor_1 interlocked?”*
* Pulse reads the codebase and provides a structured explanation, referencing specific files opened in the editor.

**Collect feedback on code quality**
* After each run, the user rates the outcome and optionally adds comments.
* Pulse logs these for future improvement/fine-tuning (locally).

---

## 7. Key Features – Agents & IDE

### 7.0 VS Code-Style IDE Experience
*Purpose: Deliver a production-quality IDE that engineers will want to use daily.*

**Layout (VS Code-inspired):**
```
┌─────────────────────────────────────────────────────────────┐
│                    Pulse - Agentic AI IDE                    │
├──────────┬──────────────────────────────────────────────────┤
│          │  [Pulse Chat] [main.st ×] [motor_ctrl.st ×]     │
│ Sidebar  │  ┌─────────────────────────────────────────────┐ │
│          │  │                                             │ │
│ • Files  │  │                                             │ │
│ • Agent  │  │         EDITOR CONTENT AREA                 │ │
│          │  │         (Tabbed Files)                      │ │
│          │  │                                             │ │
│          │  └─────────────────────────────────────────────┘ │
│  <=>     │  ═════════════════════════════════════════════   │
│          │  ┌─────────────────────────────────────────────┐ │
│          │  │ Pulse> _                                    │ │
│          │  │ TERMINAL OUTPUT                             │ │
│          │  └─────────────────────────────────────────────┘ │
└──────────┴──────────────────────────────────────────────────┘
```

* **Tabbed Editor:**
    * **Tab 0 (Permanent): "Pulse Chat"**
      * Non-closable tab for agent interactions
      * Mode selector (Agent/Plan/Ask)
      * Chat interface for natural language requests
      * Displays agent responses, plans, and validation results
    * **Dynamic File Tabs (Tab 1+):**
      * Each opened file gets its own tab with close button (×)
      * Tab header shows filename
      * Click file in sidebar → opens in new tab (or focuses if already open)
      * Supports viewing and editing PLC-style (Structured Text) code
      * Monospaced font, line numbers, syntax highlighting
      * Changes saved to disk and become context for agents

* **Workspace File Tree (Sidebar):**
    * Left panel showing workspace folder structure
    * Click file → opens in editor tab
    * New files created by Coder Agent appear automatically
    * Visual indicators for modified files

* **Integrated Terminal (Bottom Panel):**
    * Black background, monospace font
    * Terminal prompt (`Pulse> `)
    * Command history (up/down arrows)
    * Can run workspace scripts, view logs, etc.

* **Resizable Panels:**
    * **Vertical splitter:** Drag to resize sidebar ↔ main content area
    * **Horizontal splitter:** Drag to resize editor ↔ terminal
    * Splitters have visual affordance (handle/gripper)

* **Agent Panel (Sidebar):**
    * Mode selector buttons (Agent/Plan/Ask)
    * Customizer feedback section (star rating + comments)
    * Plan view for approval workflow

* **Agent-Aware Editing:**
    * Coder Agent reads files via same abstraction as editor
    * Writes changes that editor immediately reflects in tabs
    * Manual user edits are first-class: subsequent agent runs use updated file contents as ground truth

* **Safety:**
    * All edits (human or agent) constrained to configured workspace
    * Atomic writes when saving from agents to avoid partial-file corruption

### 7.1 Planner Agent (High-Context Task Planner)
*Purpose: Turn a user’s request into a concrete, step-by-step implementation plan.*

* **Inputs:** User request (natural language), Snapshot of relevant project files.
* **Outputs:** Ordered list of Plan Steps (e.g., Analyze code, Add routine, Wire logic, Document).
* **Responsibilities:**
    * Make assumptions explicit (e.g., timer resolution, input/output names).
    * Surface potential risks (“This change may affect cycle time.”).
* **UX:** Plan steps are displayed in the UI sidebar. In Plan Mode, steps require user approval.

### 7.2 Coder Agent (File I/O + Code Generation)
*Purpose: Translate plan steps into PLC-style code and actual file changes.*

* **Inputs:** Approved Plan Steps, Current workspace state.
* **Outputs:** Concrete file operations (Create/Modify files).
* **Responsibilities:**
    * Use a single PLC-like dialect (simplified Structured Text) for MVP.
    * Ensure code is idempotent (re-runnable without corruption).
    * Adhere to a simple coding style.
* **Safety:** Atomic writes constrained to the workspace.
* **Integration:** Files created/modified are immediately visible in the embedded editor.

### 7.3 Tester Agent (Validation)
*Purpose: Validate generated/modified code against the stated requirements.*

* **Inputs:** User requirement, Updated files.
* **Outputs:** Test summary (Basic static checks, Suggested test cases).
* **MVP Behavior:** Focus on static analysis and requirement coverage mapping. Optionally generate pseudo-tests.
* **UX:** Results displayed in a Test panel (e.g., “3 checks: 2 pass, 1 warning.”).

### 7.4 QA Agent (Context-Aware Q&A via RAG)
*Purpose: Answer user questions about the codebase and changes.*

* **Inputs:** User question, Vector search over project files.
* **Outputs:** Explanations referencing specific files/lines.
* **Responsibilities:** Summarize logic in human-friendly language; highlight impact of recent changes.

### 7.5 Customizer Agent (Feedback Loop & Telemetry)
*Purpose: Capture structured feedback and logs for future model improvement.*

* **Inputs:** Session metadata, User rating (1–5 stars), Optional free-text feedback.
* **Outputs:** Append-only JSONL logs stored locally.

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

* **UX:** Lightweight feedback prompt after each completed run.
* **Value:** Demonstrates a built-in fine-tuning data loop without a cloud backend.

---

## 8. Interaction Modes

### 8.1 Agent Mode (Fully Autonomous)
**Flow:** Planner → Coder → Tester → QA → Customizer

* **User experience:**
    * User enters a requirement and clicks “Run”.
    * Pulse:
        * Generates a plan (shown for transparency).
        * Edits files automatically.
        * Runs validation.
        * Summarizes what changed.
        * Prompts for feedback.
    * Updated files open or refresh in the embedded editor for inspection.
* **Use case:** Quick iteration when the user trusts the system.

### 8.2 Plan Mode (Human-in-the-Loop)
**Flow:** Planner → (User Approves Plan) → Coder → Tester → QA → Customizer

* **User experience:**
    * User enters a requirement and selects Plan Mode.
    * Planner presents a step-by-step plan.
    * User can:
        * Approve the entire plan.
        * Adjust descriptions (MVP: text edit).
    * Only then does Coder modify files.
* **Use case:** Higher-stakes changes requiring explicit review.

### 8.3 Ask Mode (Q&A Only)
**Flow:** QA → Customizer

* **User experience:**
    * User asks questions about existing code or behavior.
    * No file changes are performed.
* **Use case:** Code comprehension, impact analysis, debugging support.

---

## 9. Architecture & Stack

### 9.1 Technical Stack
* **Language:** Python 3.x
* **UI:** Flet (Python-driven, modern desktop UI with VS Code-style layout)
* **Editor:** Flet-based tabbed code editor component
  * Tab 0: Permanent "Pulse Chat" tab
  * Tabs 1+: Dynamic file tabs with close buttons
  * Monospaced font, line numbers, syntax highlighting
* **Terminal:** Flet-based integrated terminal panel
* **Orchestration:**
  * **LangGraph:** High-level multi-agent workflow and state management
  * **CrewAI/Autogen:** Agent implementation detail inside LangGraph nodes for complex sub-task execution
  * **Pattern:** LangGraph orchestrates workflow; CrewAI/Autogen handles node implementation
* **LLM Integration:**
  * Primary: OpenAI GPT-4o (for MVP agents)
  * Pluggable LLM client (future support for Anthropic, local models)
* **Persistence:**
    * SQLite for sessions and state
    * Chroma (local vector store) for RAG over project content
    * JSONL files for feedback logs
* **Packaging:** PyInstaller or flet pack for Windows .exe
* **CI/CD:** GitHub Actions (Ubuntu for tests, Windows for build)

### 9.2 High-Level Flow
1. **User interaction in "Pulse Chat" tab (Tab 0):**
   * User selects mode (Agent/Plan/Ask) in sidebar
   * User enters natural language request in Pulse Chat tab
   * User clicks "Run" or presses Enter

2. **UI → Engine:**
   * UI calls `PulseEngine.run(mode, request)` with current workspace state

3. **Engine orchestration (LangGraph):**
   * LangGraph traverses appropriate agent graph based on mode
   * Each agent node may internally use CrewAI/Autogen for complex sub-tasks
   * Agents call tools: filesystem (read/write), RAG (query), logging

4. **Engine → UI (State updates):**
   * Engine returns updated `PulseState` (plan, file changes, test results, answers)

5. **UI rendering updates:**
   * **Pulse Chat tab:** Display agent responses, plans, validation results
   * **File tree:** Refresh with new/modified files
   * **File tabs:** Open modified files in new tabs (or refresh if already open)
   * **Terminal:** Log agent activity, show command outputs
   * **Agent panel:** Show feedback prompt (star rating + comments)

6. **User review and iteration:**
   * User reviews changes in file tabs
   * User can manually edit code in tabs
   * User can provide feedback via Agent panel
   * User can ask follow-up questions in Pulse Chat tab

---

## 10. Operational Excellence – Deployment & CI/CD

### 10.1 Objectives
Ensure every change is:
* Tested before being packaged.
* Packaged automatically into a Windows .exe.
* Published in a repeatable, observable way.

### 10.2 CI/CD Pipeline (GitHub Actions)
**Triggers:**
* **On every push / PR to main:** Run linting and unit tests.
* **On tag (e.g., v0.1.0):** Run tests, Build .exe for Windows, Attach binary to a GitHub Release.

**Jobs:**
1. **lint_and_test (Ubuntu)**
    * Install Python, dependencies.
    * Run:
        * Static analysis (e.g., ruff).
        * Unit tests (pytest) for: Engine logic, Filesystem tools, Persistence & logging.
2. **build_windows (Windows)**
    * Install Python, dependencies.
    * Build desktop executable: `pyinstaller` or `flet pack` on `main.py`.
    * Upload artifact.
3. **release (Ubuntu)**
    * For tagged versions: Create GitHub Release.
    * Attach the Windows artifact.

**Value for Stakeholder:**
* Clear “green pipeline” as a visible signal of quality.
* Reproducible builds—no manual packaging.
* Easy distribution: link to GitHub Release with a downloadable installer.

---

## 11. Non-Functional Requirements

### 11.1 Privacy & Security
* All project files stay on user’s local machine by default.
* No automatic upload of code, logs, or PLC projects to external services.
* **LLM calls:**
    * Configurable using API keys.
    * Clear documentation of what is sent to LLM providers (e.g., truncated context).

### 11.2 Performance & Latency
* **App startup:** < 5 seconds on a typical engineering laptop.
* **Core interactions:**
    * Simple Q&A responses: target < 5 seconds (excluding LLM latency).
    * Full agent run (Planner → Coder → Tester) for small projects: < 20–30 seconds.
* The UI must remain responsive during long agent runs (non-blocking).

### 11.3 Reliability
* No destructive file operations outside the configured workspace.
* Atomic writes when modifying files (write to temp + rename).
* **Recoverable state:**
    * Most recent session can be reloaded on app restart.
    * Graceful handling of: LLM failures (timeouts, quota), Corrupted or missing files.

### 11.4 Usability
* Clear visual distinction between: Plan steps, File changes, Test results.
* Persistent mode selector (Agent / Plan / Ask).
* Basic error messaging (“LLM request failed, please retry.”).
* Embedded editor that makes Pulse feel like a familiar IDE: Readable font, line numbers, clear active file highlighting.

### 11.5 Extensibility
* Agent graph and tools are modular.
* New agents (e.g., “Refactor Agent”) can be added without UI redesign.
* Additional PLC dialects can be supported behind a configuration flag in future versions.

---

## 12. Success Metrics

### 12.1 Delivery & Execution
* **Delivery timeline:** Fully functional IDE with MVP agents within 7 days (~140 hours)
* **CI pipeline health:** ≥ 90% of pushes to main have all checks green
* **Automated test coverage:** Unit tests covering:
    * Core agent orchestration (LangGraph workflows)
    * File system operations (atomic writes, workspace management)
    * Persistence & logging (SQLite, JSONL, Chroma)
    * UI components (tab management, file tree, terminal)

### 12.2 Product Experience (Qualitative)
A reviewer (e.g., hiring manager) can:

1. **Install and launch:**
   * Download and run Pulse .exe from GitHub Release
   * App launches in < 5 seconds

2. **Experience VS Code-style IDE:**
   * Open workspace folder
   * Navigate file tree in left sidebar
   * Click file → opens in new tab with close button (×)
   * See permanent "Pulse Chat" tab (Tab 0)
   * Resize panels by dragging splitters (sidebar, terminal)
   * View/edit code with syntax highlighting and line numbers
   * Use integrated terminal at bottom

3. **Complete end-to-end agent flows:**
   * **Agent Mode:**
     * Enter request in Pulse Chat tab
     * Watch plan generation in real-time
     * See files automatically created/modified and opened in tabs
     * Review test summary
     * Provide feedback via Agent panel
   * **Plan Mode:**
     * Enter request in Pulse Chat tab
     * Review step-by-step plan in sidebar
     * Approve plan
     * Watch code changes apply
     * Inspect changes in file tabs
   * **Ask Mode:**
     * Ask question about codebase
     * Receive explanation with file references
     * Click references to open files in tabs

4. **Manual editing integration:**
   * Make manual edits to code in tabs
   * Run agent on same file
   * Verify agent uses updated content as ground truth

**Perception benchmarks:**
* "This is a production-quality IDE I would actually use daily"
* "The tabbed editor and terminal feel as polished as VS Code"
* "The agent integration is seamless - it enhances my workflow without getting in the way"
* "The deployment and build process is clearly thought-through"

### 12.3 Operational Excellence
* **Build success rate:** ≥ 95% of tagged releases result in a successful .exe build and attached artifact.
* **Mean Time to Fix (MTTF) for broken builds:** Broken main-branch builds are corrected within one working session.

---

## 13. Risks & Assumptions

**Assumptions**
* OpenAI GPT-4o API is available for MVP agent implementation
* User has valid OpenAI API key configured
* User has permission to run local executables and install dependencies
* Target PLC use-case can be represented in a simplified Structured Text-like dialect
* Flet framework supports required UI features (tabs, terminal, resizable splitters)

**Risks**
* **UI complexity vs timeline:**
  * Building VS Code-level IDE in 7 days with Flet is ambitious
  * *Mitigation:* Focus on core IDE features (tabs, terminal, splitters); defer advanced features (themes, keybindings, extensions)

* **LLM variability:**
  * GPT-4o may produce inconsistent code quality
  * *Mitigation:* Use Tester Agent for validation; Plan Mode for human review; CrewAI/Autogen for multi-step refinement

* **CrewAI/Autogen integration:**
  * Integrating two orchestration frameworks (LangGraph + CrewAI/Autogen) adds complexity
  * *Mitigation:* Clear separation - LangGraph for workflow, CrewAI/Autogen only inside nodes; keep node interfaces simple

* **User trust:**
  * Engineers may be cautious about letting AI edit PLC code
  * *Mitigation:* Provide Plan Mode, clear visibility via tabbed editor, atomic writes, workspace constraints

* **Packaging friction:**
  * PyInstaller/flet pack may struggle with complex dependencies (LangGraph, CrewAI, Chroma)
  * *Mitigation:* Test packaging early; consider flet pack (designed for Flet apps); test on clean Windows VM

* **Terminal implementation:**
  * Building functional terminal in Flet may have limitations
  * *Mitigation:* Keep terminal simple (command execution + output display); defer advanced features (REPL, shell integration)