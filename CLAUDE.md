# Pulse IDE - Agentic AI IDE for PLC Coding

## What is Pulse?
Pulse is a **Windows desktop IDE** (built with Python + Flet) that uses AI agents to help automation engineers write PLC code. Think "Claude Code for industrial automation" - users describe what they want in natural language, and an AI agent generates/modifies Structured Text (.st) code.

## Architecture: Hub-and-Spoke with LangGraph

```
User Input (Pulse Chat)
       ↓
┌──────────────────────────────────────────┐
│         MASTER AGENT (LangGraph)          │
│  ┌─────────────────┐   ┌───────────────┐ │
│  │ master_agent_   │◄─►│ tool_execution│ │
│  │     node        │   │     _node     │ │
│  └─────────────────┘   └───────────────┘ │
└──────────────────────────────────────────┘
       ↓                        ↓
   LLM Decision            Tool Belt
   (GPT/Claude)         (3-tier tools)
```

**Single Agent, Multiple Tools:** One Master Agent makes all decisions. Tools are organized in 3 tiers:
- **Tier 1 (Atomic):** `manage_file_ops`, `apply_patch`, `search_workspace`
- **Tier 2 (Permissioned):** `run_terminal_cmd`, `dependency_manager` (require user approval)
- **Tier 3 (Agentic):** `web_search`, `implement_feature` (CrewAI), `diagnose_project` (AutoGen)

**3 Modes:** Same agent, different system prompts:
- **Agent Mode:** Full tool access, can modify files
- **Ask Mode:** Read-only, can search/explore
- **Plan Mode:** Planning only, no execution

## Key Files

| File | Purpose |
|------|---------|
| `src/agents/master_graph.py` | LangGraph workflow with 2 nodes (master_agent_node, tool_execution_node) |
| `src/agents/runtime.py` | Entry point: `run_agent()`, handles single-run enforcement |
| `src/agents/state.py` | `MasterState` TypedDict, `PatchPlan`, `CommandPlan` models |
| `src/core/prompts.py` | System prompts for Agent/Ask/Plan modes + PLC enhancement |
| `src/core/llm_client.py` | LLM abstraction for OpenAI + Anthropic with function calling |
| `src/tools/registry.py` | Tool registration, schemas, invocation |
| `src/ui/app.py` | Main Flet application (VS Code-style layout) |
| `src/ui/editor.py` | Tabbed editor with syntax highlighting |
| `src/ui/bridge.py` | Event bus connecting backend to UI |
| `src/ui/components/approval.py` | Patch/terminal approval modals |

## Constraints (Non-Negotiable)

1. **Windows Desktop Only** - Local-first, no cloud backend
2. **Flet UI** - No web frameworks (React/Vue)
3. **LangGraph Orchestration** - Keep for future complex workflows
4. **Human-in-the-Loop** - User must approve patches and terminal commands
5. **Single Active Run** - Only one agent execution at a time

## Current Goal

Make Pulse achieve Claude Code-level quality through improvements in:
1. Tool execution (process all tool calls per iteration)
2. Prompts (ReAct + CoT patterns)
3. Memory management (intelligent summarization)
4. UI polish (Monaco editor integration)

**See `docs/TASK_INDEX.md` for detailed implementation tasks.**
