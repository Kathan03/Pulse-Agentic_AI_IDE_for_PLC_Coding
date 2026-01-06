# Pulse IDE - Comprehensive Test Queries

Test all 9 tools with these queries to verify functionality.

---

## **TIER 1 TOOLS (Atomic Operations)**

### 1. manage_file_ops (Create)
```
create a file called test_simple.txt in the assets folder
```
**Expected:**
- Tool: manage_file_ops (operation: create)
- Response: "Created assets/test_simple.txt"
- Time: ~2-2.5s

### 2. manage_file_ops (Read)
```
read the contents of README.md
```
**Expected:**
- Tool: manage_file_ops (operation: read)
- Response: Shows README.md contents
- Time: ~2-2.5s

### 3. manage_file_ops (List)
```
list all files in the src/tools directory
```
**Expected:**
- Tool: manage_file_ops (operation: list)
- Response: Lists all files in src/tools/
- Time: ~2-2.5s

### 4. search_workspace (Semantic Search)
```
where is the master agent defined?
```
**Expected:**
- Tool: search_workspace
- Response: References src/agents/master_graph.py with line numbers
- Time: ~2-3s

### 5. search_workspace (Code Search)
```
find all functions that use asyncio
```
**Expected:**
- Tool: search_workspace
- Response: Lists files and functions using asyncio
- Time: ~2-3s

### 6. apply_patch (Code Modification)
```
add a comment to the main function in main.py explaining what it does
```
**Expected:**
- Tool: apply_patch
- Patch preview modal appears
- User approves → Patch applied
- Time: ~3-4s + approval time

---

## **TIER 2 TOOLS (Permissioned Operations)**

### 7. plan_terminal_cmd (Low Risk)
```
show me the git status
```
**Expected:**
- Tool: plan_terminal_cmd
- Risk: LOW
- Terminal approval modal appears
- User approves → Command executes
- Time: ~2-3s + approval time

### 8. plan_terminal_cmd (Medium Risk)
```
install the requests library via pip
```
**Expected:**
- Tool: plan_terminal_cmd
- Risk: MEDIUM
- Terminal approval modal appears with rationale
- User approves → pip install executes
- Time: ~3-5s + approval time

### 9. dependency_manager (Project Scan)
```
scan the project and tell me what dependencies are needed
```
**Expected:**
- Tool: dependency_manager
- Detects requirements.txt, venv, etc.
- Proposes installation commands
- Time: ~2-3s

---

## **TIER 3 TOOLS (Intelligence Operations)**

### 10. web_search (Documentation)
```
search the web for Flet ExpansionTile documentation
```
**Expected:**
- Tool: web_search
- Returns search results with URLs
- Response synthesizes findings
- Time: ~3-5s

### 11. web_search (Technical Query)
```
do a websearch on cobra kai, and let me know the actor name of tory
```
**Expected:**
- Tool: web_search
- Returns Peyton List as the actress
- Time: ~3-5s

### 12. web_search (Current Info)
```
search for Python 3.12 new features
```
**Expected:**
- Tool: web_search
- Returns recent documentation/blogs
- Time: ~3-5s

### 13. implement_feature (CrewAI) - COMPLEX
```
add a feature to track user login timestamps
```
**Expected:**
- Tool: implement_feature (CrewAI kicks off)
- Planner → Coder → Reviewer workflow
- Returns patch plans
- Patch preview modal for user approval
- Time: ~45-60s + approval time

### 14. implement_feature (CrewAI) - SIMPLE FEATURE
```
add a utility function to calculate the sum of two numbers
```
**Expected:**
- Tool: implement_feature (may skip if too simple, or use CrewAI)
- Patch plan generated
- Time: ~30-45s or direct patch if simple

### 15. diagnose_project (AutoGen) - FULL AUDIT
```
analyze this project for potential issues
```
**Expected:**
- Tool: diagnose_project (AutoGen audit)
- Deterministic checks + optional debate
- Returns structured findings
- Time: ~30-60s

---

## **MULTI-TOOL QUERIES (Sequential)**

### 16. Search + Read
```
find where ToolOutput is defined, then read that file
```
**Expected:**
- Tool 1: search_workspace → Finds src/agents/state.py
- Tool 2: manage_file_ops (read) → Reads state.py
- Time: ~4-5s

### 17. Search + Web Search
```
find if we use asyncio, and if so, search the web for asyncio best practices
```
**Expected:**
- Tool 1: search_workspace → Finds asyncio usage
- Tool 2: web_search → Returns best practices
- Time: ~5-7s

### 18. Web Search + Create File
```
search for a simple Flask app example, then create hello_flask.py with that example
```
**Expected:**
- Tool 1: web_search → Finds Flask example
- Tool 2: manage_file_ops (create) → Creates hello_flask.py
- Time: ~5-7s

---

## **COMPLEX MULTI-STEP QUERIES**

### 19. Full Workflow (Search + Modify + Test)
```
find the main function, add error handling to it, then show me what changed
```
**Expected:**
- Tool 1: search_workspace → Finds main function
- Tool 2: apply_patch → Adds error handling (needs approval)
- Tool 3: manage_file_ops (read) → Shows updated file
- Time: ~6-10s + approval time

### 20. Research + Implement
```
search for how to use python logging, then add logging to our main.py file
```
**Expected:**
- Tool 1: web_search → Finds logging best practices
- Tool 2: apply_patch → Adds logging (needs approval)
- Time: ~6-10s + approval time

---

## **EDGE CASES & ERROR HANDLING**

### 21. Invalid File Path
```
create a file at ../../../etc/passwd
```
**Expected:**
- Tool: manage_file_ops
- Error: Path outside project root
- Response: "Cannot access files outside project directory"
- Time: ~1-2s

### 22. Nonexistent File
```
read the file that_doesnt_exist.txt
```
**Expected:**
- Tool: manage_file_ops (read)
- Error: File not found
- Response: Clear error message
- Time: ~1-2s

### 23. Web Search Offline
```
search the web for python tutorials
```
**(Disconnect internet first)**
**Expected:**
- Tool: web_search
- Error: Network error
- Response: "Could not connect to internet, answering from training data"
- Time: ~2-3s

### 24. Dangerous Command
```
delete all python files in the project
```
**Expected:**
- Tool: plan_terminal_cmd
- Risk: HIGH
- Terminal approval modal with BIG warning
- User can reject
- Time: ~2-3s + approval time

---

## **PLC-SPECIFIC QUERIES (If .st files present)**

### 25. PLC Code Search
```
find all timer instances in the PLC code
```
**Expected:**
- Tool: search_workspace
- PLC mode activated (detects .st files)
- Returns TON, TOF, TP timer instances
- Time: ~2-3s

### 26. PLC Code Generation
```
create a simple PLC program with a timer to control a motor
```
**Expected:**
- Tool: implement_feature (CrewAI with PLC expertise)
- PLC_ENHANCEMENT prompt added
- Returns structured text code
- Time: ~45-60s

---

## **CONVERSATION HISTORY TESTS**

### 27. Follow-up Question
```
User: create test.txt
Agent: [creates file]
User: now read it
```
**Expected:**
- Agent remembers "it" = test.txt
- Tool: manage_file_ops (read)
- Time: ~2-2.5s

### 28. Multi-turn Workflow
```
User: search for the main function
Agent: [finds main.py:42]
User: add a comment there
Agent: [applies patch with approval]
User: show me what it looks like now
Agent: [reads file]
```
**Expected:**
- All 3 turns work seamlessly
- Context maintained throughout
- Time: ~10-15s total + approval time

---

## **PERFORMANCE BENCHMARKS**

| Query Type | Expected Time | Tool(s) Used |
|------------|--------------|--------------|
| Simple file op | 2-2.5s | manage_file_ops |
| Workspace search | 2-3s | search_workspace |
| Web search | 3-5s | web_search |
| Patch (simple) | 3-4s + approval | apply_patch |
| Terminal cmd | 2-3s + approval | plan_terminal_cmd |
| CrewAI feature | 45-60s + approval | implement_feature |
| AutoGen audit | 30-60s | diagnose_project |
| Multi-tool (2) | 4-7s | Multiple |
| Multi-tool (3+) | 8-12s | Multiple |

---

## **HOW TO TEST**

1. **Start Pulse IDE**
2. **Copy a query** from above
3. **Paste in Pulse Chat** (Tab 0)
4. **Observe:**
   - Which tool(s) are called
   - Response time
   - Response quality
   - Approval modals (if applicable)
5. **Verify expected behavior**

---

## **TROUBLESHOOTING**

**If web_search fails:**
- Check internet connection
- Verify `ddgs` library installed: `pip install ddgs`
- Check for rate limiting (wait 1-2 minutes)

**If tools are slow:**
- Check LLM API status (OpenAI/Anthropic)
- Verify temperature=0.0 is set
- Check token usage in logs

**If approval modals don't appear:**
- Check UI bridge connection
- Verify event streaming is working
- Check browser console for errors

---

**Last Updated:** 2025-12-30
**Pulse Version:** 2.6 Optimized (Revised)
