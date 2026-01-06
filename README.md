
  You are a senior AI engineer implementing real LLM integration for Pulse IDE. The stub LLM (call_llm_stub) blocks all agent functionality - replace it with OpenAI + Anthropic clients supporting function calling. Follow docs/PHASE_1_PROMPT.md for requirements; CLAUDE.md has architecture context.

  ---
  Phase 2: Architecture Cleanup

  You are a software architect refactoring Pulse to match Claude Code's proven architecture. DELETE src/core/context_manager.py entirely - it causes static classification that breaks hybrid projects (Python+PLC+JS). Follow docs/PHASE_2_PROMPT.md to implement dynamic workspace discovery via tools instead.

  ---
  Phase 3: Web Search Tool

  You are a backend engineer adding web search to Pulse's Tool Belt. Master Agent currently can't answer documentation questions - add DuckDuckGo integration (Tier 3) so it can research Flet docs, PLC manuals, Stack Overflow. Follow docs/PHASE_3_PROMPT.md for implementation.

  ---
  Phase 4: UI Fixes & Polish

  You are a UI/UX engineer fixing critical bugs in Pulse's Flet interface. Sidebar doesn't scroll, menu bar invisible, file tree is flat, model dropdown outdated - fix these to match VS Code quality. Follow docs/PHASE_4_PROMPT.md; verify all Flet attributes against official docs.

  ---
  Phase 5: Testing & Production Release

  You are a QA engineer validating Pulse v1.0 for production. Execute comprehensive end-to-end tests: LLM integration, mode switching (Agent/Ask/Plan), PLC code generation, approval gates. Follow docs/PHASE_5_PROMPT.md test suite; all criteria must pass before v1.0 release.

  #Issue
  1. Prompt changes needs to be done. The agent response are too inconsistent. And something completely different to the expected response. It is too focused towards PLC coding so its not doing any normal task
  2. Check if the master agent can really access all the tools.
  3. Check if agent ask for permission before editing anything. How is the UI to check the code changes? 
  4. UI issues (Mostly solved)
  5. Push on github
  6. Github actions CI/CD


I want to thoroughly analyze the difference between Pulse and Cursor/Claude-code. This includes the Agentic AI implementation and also how should I improve the UI?

Let's just finalize the things we need to do for this application to reach claude-code/cursor level. Starting with finalizing the architecture? Is the current architecture good enough? Is it similar to claude-code's architecture? If the architecture is correct then what other issues are present which forbids this application to become claude-code like? Is it the prompt? Tools? Memory is not preserved in a conversation or the long-term

For architecture and prompts I need a detailed explaination on how my architecture is different than claude-code? I know that claude-code uses a simple loop and an LLM can only return either a generated response or a response from a tool at a given time, so are the number of tool calls same in my architecture and claude code? Also, I am using Langraph, should I switch to simple loop? Is the issue why this application is not a claude-code's level is the prompts? Will improving prompts to ReAct + CoT design patterns improve the performance?

I know I am using a differnt cheaper model, which I will change later, so ignore that. Apart from the model what is the main reason for the difference? 

Apart from the architecture and Agentic AI implementation, many other UI components are not implemented properly. Please let me know what the following files purpose are:
1. approval.py
2. clarification.py
3. code_preview_panel.py
4. loading_animation.py
5. vibe_loader.py
6. settings_modal.py
7. bridge.py

Also, currently the code editor is not working properly so I am going to embed monaco editor in my product. This monaco will be used for code_preview_panel (showing the code diff (current vs Pulse suggested)), and the editor.py file will also be embeded with monaco. Based on the current code implementation, and what I want with monaco, which files needs to be deleted? 

Please read all the necessary files throughly to answer my questions (Do not assume the contents of the files to answer). Before you begin, acknowledge what I need you to do.