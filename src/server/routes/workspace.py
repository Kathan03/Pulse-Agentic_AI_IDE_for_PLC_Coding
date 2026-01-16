"""
Workspace management routes for Pulse IDE.

Provides API endpoints for workspace initialization and management.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from pathlib import Path
import logging

from src.core.workspace import ensure_workspace_initialized

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


class InitWorkspaceRequest(BaseModel):
    """Request model for workspace initialization."""
    project_root: str


class InitWorkspaceResponse(BaseModel):
    """Response model for workspace initialization."""
    success: bool
    initialized: bool
    pulse_dir: str
    message: str


@router.post("/init", response_model=InitWorkspaceResponse)
async def init_workspace(request: InitWorkspaceRequest):
    """
    Initialize .pulse directory for a workspace.
    
    This endpoint should be called when a folder is opened in the IDE.
    It creates the .pulse/ directory with all necessary subdirectories
    and database files.
    
    Args:
        request: Contains project_root path.
        
    Returns:
        InitWorkspaceResponse with initialization status.
    """
    try:
        project_path = Path(request.project_root)
        
        if not project_path.exists():
            return InitWorkspaceResponse(
                success=False,
                initialized=False,
                pulse_dir="",
                message=f"Project root does not exist: {request.project_root}"
            )
        
        if not project_path.is_dir():
            return InitWorkspaceResponse(
                success=False,
                initialized=False,
                pulse_dir="",
                message=f"Project root is not a directory: {request.project_root}"
            )
        
        # Initialize workspace
        manager = ensure_workspace_initialized(request.project_root)
        
        logger.info(f"Workspace initialized: {request.project_root}")
        
        return InitWorkspaceResponse(
            success=True,
            initialized=manager.is_initialized(),
            pulse_dir=str(manager.pulse_dir),
            message="Workspace initialized successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to initialize workspace: {e}")
        return InitWorkspaceResponse(
            success=False,
            initialized=False,
            pulse_dir="",
            message=f"Error: {str(e)}"
        )
