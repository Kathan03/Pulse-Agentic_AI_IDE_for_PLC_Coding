"""
QA Agent Node for Pulse IDE.

Handles "Ask Mode" - answers user questions about the codebase
without modifying any files. Uses RAG (Retrieval-Augmented Generation)
to provide context-aware responses.
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.core.state import AgentState
from src.core.chroma_db_rag import get_rag
from src.core.config import Config


def qa_node(state: AgentState) -> Dict[str, Any]:
    """
    QA Agent Node for answering user questions.

    This node:
    1. Extracts the user's question from state
    2. Performs RAG retrieval to find relevant code snippets
    3. Uses an LLM to synthesize a helpful answer
    4. Returns the answer in the messages list

    Args:
        state: Current agent state containing user_request and context.

    Returns:
        Dict with updated messages containing the AI's answer.

    Example:
        >>> state = {"user_request": "What does the MotorControl function do?", ...}
        >>> result = qa_node(state)
        >>> print(result["messages"][-1].content)
    """
    # Extract user request
    user_request = state.get("user_request", "")

    if not user_request:
        return {
            "messages": [
                AIMessage(content="No question provided. Please ask a question about the codebase.")
            ]
        }

    # Step 1: RAG Retrieval
    try:
        rag = get_rag()
        search_results = rag.search_codebase(query=user_request, n_results=5)
    except Exception as e:
        # If RAG fails (e.g., empty collection), proceed without context
        print(f"RAG search failed: {e}")
        search_results = []

    # Step 2: Build context from search results
    if search_results:
        context_parts = []
        for i, result in enumerate(search_results, 1):
            file_path = result.get("metadata", {}).get("path", "unknown")
            content = result.get("content", "")
            context_parts.append(
                f"--- File: {file_path} ---\n{content}\n"
            )
        context = "\n".join(context_parts)
    else:
        context = "No relevant code found in the codebase."

    # Step 3: Synthesize answer using LLM
    llm = ChatOpenAI(
        model=Config.OPENAI_MODEL_NAME,
        api_key=Config.OPENAI_API_KEY,
        temperature=0.3  # Lower temperature for more focused answers
    )

    system_prompt = SystemMessage(
        content=(
            "You are Pulse, a helpful PLC coding assistant with expertise in IEC 61131-3 "
            "Structured Text programming. Answer the user's question based STRICTLY on the "
            "provided codebase context. If the context doesn't contain enough information, "
            "say so clearly. Provide file references (e.g., 'in main.st') when mentioning code. "
            "Be concise and technical."
        )
    )

    user_message = HumanMessage(
        content=(
            f"QUESTION: {user_request}\n\n"
            f"CODEBASE CONTEXT:\n{context}\n\n"
            f"Please answer the question based on the context above."
        )
    )

    try:
        response = llm.invoke([system_prompt, user_message])
        answer = response.content
    except Exception as e:
        answer = f"Error generating answer: {str(e)}"

    # Step 4: Return updated state with answer
    return {
        "messages": [AIMessage(content=answer)],
        "file_context": context  # Store context for potential follow-up
    }
