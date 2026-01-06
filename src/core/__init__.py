"""
Core module for Pulse IDE.
"""

from src.core.events import (
    Event,
    EventType,
    EventBus,
    get_event_bus,
    emit_status,
    emit_node_entered,
    emit_node_exited,
    emit_tool_requested,
    emit_tool_executed,
    emit_approval_requested,
    emit_approval_granted,
    emit_approval_denied,
    emit_run_started,
    emit_run_completed,
    emit_run_cancelled,
)

from src.core.analytics import (
    ToolAnalytics,
    get_analytics,
    log_tool_usage,
    get_analytics_summary,
    reset_analytics,
)

__all__ = [
    # Events
    "Event",
    "EventType",
    "EventBus",
    "get_event_bus",
    "emit_status",
    "emit_node_entered",
    "emit_node_exited",
    "emit_tool_requested",
    "emit_tool_executed",
    "emit_approval_requested",
    "emit_approval_granted",
    "emit_approval_denied",
    "emit_run_started",
    "emit_run_completed",
    "emit_run_cancelled",
    
    # Analytics
    "ToolAnalytics",
    "get_analytics",
    "log_tool_usage",
    "get_analytics_summary",
    "reset_analytics",
]
