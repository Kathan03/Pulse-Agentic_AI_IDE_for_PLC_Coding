"""
Conversations API Routes.

Provides REST endpoints for conversation management:
- GET /api/conversations - List recent conversations
- POST /api/conversations - Create new conversation
- GET /api/conversations/{id} - Get conversation details
- DELETE /api/conversations/{id} - Delete conversation
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

from src.core.db import ConversationDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

# Default project root (will be set from workspace)
_project_root: Optional[str] = None


def set_project_root(path: str) -> None:
    """Set the project root for database operations."""
    global _project_root
    _project_root = path
    logger.info(f"Conversations API project root set to: {path}")


def get_db() -> ConversationDB:
    """Get database instance for current project."""
    if not _project_root:
        raise HTTPException(status_code=400, detail="No project is open")
    return ConversationDB(_project_root)


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateConversationRequest(BaseModel):
    title: Optional[str] = None


class ConversationResponse(BaseModel):
    id: str
    title: Optional[str]
    created_at: str
    updated_at: str
    message_count: Optional[int] = None


# ============================================================================
# Routes
# ============================================================================

@router.get("")
async def list_conversations(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get recent conversations for the current project.
    
    Returns list of conversations with title and timestamps.
    """
    try:
        db = get_db()
        conversations = db.get_recent_conversations(limit=limit)
        
        # Add message counts
        for conv in conversations:
            conv["message_count"] = db.get_message_count(conv["id"])
        
        return conversations
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_conversation(request: CreateConversationRequest) -> Dict[str, Any]:
    """
    Create a new conversation.
    
    Returns the new conversation's ID and metadata.
    """
    try:
        db = get_db()
        conversation_id = db.create_conversation(title=request.title)
        conversation = db.get_conversation(conversation_id)
        
        return {
            "success": True,
            "conversation": conversation
        }
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str) -> Dict[str, Any]:
    """
    Get a conversation with its messages.
    """
    try:
        db = get_db()
        conversation = db.get_conversation(conversation_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = db.get_messages(conversation_id)
        
        return {
            "conversation": conversation,
            "messages": messages
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str) -> Dict[str, Any]:
    """
    Delete a conversation and all its messages.
    """
    try:
        db = get_db()
        success = db.delete_conversation(conversation_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete conversation")
        
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
