"""
Tool Usage Analytics for Pulse IDE.

Tracks tool execution patterns for optimization insights:
- Which tools are used most frequently
- Success/failure rates per tool
- Execution duration for identifying slow tools
- Common patterns and failure modes

Data is stored in .pulse/analytics.json within the project workspace.

Example:
    >>> from src.core.analytics import get_analytics, log_tool_usage
    >>> log_tool_usage("search_workspace", success=True, duration_ms=150)
    >>> summary = get_analytics_summary()
    >>> print(summary["total_calls"])  # 1
"""

import json
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# ANALYTICS DATA STRUCTURE
# ============================================================================

DEFAULT_ANALYTICS = {
    "version": "1.0",
    "created_at": None,
    "updated_at": None,
    "tool_calls": [],
    "summary": {
        "total_calls": 0,
        "total_success": 0,
        "total_failures": 0,
        "by_tool": {}
    }
}


# ============================================================================
# THREAD-SAFE ANALYTICS CLASS
# ============================================================================

class ToolAnalytics:
    """
    Thread-safe tool usage analytics manager.
    
    Provides atomic read/write operations for analytics data
    with automatic persistence to JSON.
    
    Attributes:
        project_root: Project root directory containing .pulse folder.
        analytics_file: Path to analytics.json file.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize analytics manager.
        
        Args:
            project_root: Project root directory. If None, uses current directory.
        """
        self._lock = threading.Lock()
        self._project_root = project_root or Path.cwd()
        self._analytics_file = self._project_root / ".pulse" / "analytics.json"
        self._data: Optional[Dict[str, Any]] = None
        
    @property
    def analytics_file(self) -> Path:
        """Get path to analytics file."""
        return self._analytics_file
    
    def load(self) -> Dict[str, Any]:
        """
        Load analytics data from file.
        
        Returns:
            Analytics data dict. Creates default if file doesn't exist.
        """
        with self._lock:
            if self._data is not None:
                return self._data
            
            if self._analytics_file.exists():
                try:
                    self._data = json.loads(self._analytics_file.read_text(encoding="utf-8"))
                    logger.debug(f"Loaded analytics from {self._analytics_file}")
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Failed to load analytics, creating new: {e}")
                    self._data = self._create_default()
            else:
                self._data = self._create_default()
                
            return self._data
    
    def _create_default(self) -> Dict[str, Any]:
        """Create default analytics data structure."""
        data = DEFAULT_ANALYTICS.copy()
        data["summary"] = DEFAULT_ANALYTICS["summary"].copy()
        data["summary"]["by_tool"] = {}
        data["tool_calls"] = []
        data["created_at"] = datetime.now().isoformat()
        data["updated_at"] = datetime.now().isoformat()
        return data
    
    def save(self) -> bool:
        """
        Save analytics data to file.
        
        Returns:
            True if saved successfully, False otherwise.
        """
        with self._lock:
            if self._data is None:
                return False
            
            try:
                # Ensure .pulse directory exists
                self._analytics_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Update timestamp
                self._data["updated_at"] = datetime.now().isoformat()
                
                # Write atomically (write to temp then rename)
                temp_file = self._analytics_file.with_suffix(".tmp")
                temp_file.write_text(
                    json.dumps(self._data, indent=2),
                    encoding="utf-8"
                )
                temp_file.replace(self._analytics_file)
                
                logger.debug(f"Saved analytics to {self._analytics_file}")
                return True
                
            except IOError as e:
                logger.error(f"Failed to save analytics: {e}")
                return False
    
    def log_tool_usage(
        self,
        tool_name: str,
        success: bool,
        duration_ms: int,
        error: Optional[str] = None
    ) -> None:
        """
        Log a tool execution event.
        
        Args:
            tool_name: Name of the tool that was executed.
            success: Whether the execution succeeded.
            duration_ms: Execution duration in milliseconds.
            error: Error message if failed (optional).
        """
        data = self.load()
        
        with self._lock:
            # Add to call log (keep last 1000 calls to prevent unbounded growth)
            call_record = {
                "tool": tool_name,
                "success": success,
                "duration_ms": duration_ms,
                "timestamp": datetime.now().isoformat()
            }
            if error:
                call_record["error"] = error[:200]  # Truncate long errors
            
            data["tool_calls"].append(call_record)
            
            # Trim to last 1000 calls
            if len(data["tool_calls"]) > 1000:
                data["tool_calls"] = data["tool_calls"][-1000:]
            
            # Update summary stats
            data["summary"]["total_calls"] += 1
            if success:
                data["summary"]["total_success"] += 1
            else:
                data["summary"]["total_failures"] += 1
            
            # Update per-tool stats
            if tool_name not in data["summary"]["by_tool"]:
                data["summary"]["by_tool"][tool_name] = {
                    "calls": 0,
                    "success": 0,
                    "failures": 0,
                    "total_duration_ms": 0,
                    "avg_duration_ms": 0
                }
            
            tool_stats = data["summary"]["by_tool"][tool_name]
            tool_stats["calls"] += 1
            tool_stats["total_duration_ms"] += duration_ms
            if success:
                tool_stats["success"] += 1
            else:
                tool_stats["failures"] += 1
            
            # Recalculate average
            tool_stats["avg_duration_ms"] = tool_stats["total_duration_ms"] // tool_stats["calls"]
        
        # Save after each log (can be optimized with batching if needed)
        self.save()
        
        logger.debug(f"[E3] Logged tool usage: {tool_name} (success={success}, duration={duration_ms}ms)")
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get analytics summary.
        
        Returns:
            Dict with aggregated statistics:
            - total_calls: Total tool invocations
            - total_success: Successful invocations
            - total_failures: Failed invocations
            - success_rate: Overall success percentage
            - by_tool: Per-tool breakdown
        """
        data = self.load()
        summary = data["summary"].copy()
        
        # Calculate success rate
        if summary["total_calls"] > 0:
            summary["success_rate"] = round(
                (summary["total_success"] / summary["total_calls"]) * 100, 1
            )
        else:
            summary["success_rate"] = 0.0
        
        return summary
    
    def get_slow_tools(self, threshold_ms: int = 1000) -> List[Dict[str, Any]]:
        """
        Get tools that exceed duration threshold.
        
        Args:
            threshold_ms: Duration threshold in milliseconds.
            
        Returns:
            List of tool stats for tools exceeding threshold.
        """
        summary = self.get_summary()
        slow_tools = []
        
        for tool_name, stats in summary.get("by_tool", {}).items():
            if stats.get("avg_duration_ms", 0) > threshold_ms:
                slow_tools.append({
                    "tool": tool_name,
                    "avg_duration_ms": stats["avg_duration_ms"],
                    "calls": stats["calls"]
                })
        
        return sorted(slow_tools, key=lambda x: x["avg_duration_ms"], reverse=True)
    
    def get_failing_tools(self, min_failure_rate: float = 0.1) -> List[Dict[str, Any]]:
        """
        Get tools with high failure rates.
        
        Args:
            min_failure_rate: Minimum failure rate (0.0 to 1.0) to include.
            
        Returns:
            List of tool stats for tools with high failure rates.
        """
        summary = self.get_summary()
        failing_tools = []
        
        for tool_name, stats in summary.get("by_tool", {}).items():
            calls = stats.get("calls", 0)
            failures = stats.get("failures", 0)
            if calls > 0:
                failure_rate = failures / calls
                if failure_rate >= min_failure_rate:
                    failing_tools.append({
                        "tool": tool_name,
                        "failure_rate": round(failure_rate * 100, 1),
                        "failures": failures,
                        "calls": calls
                    })
        
        return sorted(failing_tools, key=lambda x: x["failure_rate"], reverse=True)
    
    def reset(self) -> None:
        """Reset all analytics data."""
        with self._lock:
            self._data = self._create_default()
        self.save()
        logger.info("[E3] Analytics data reset")


# ============================================================================
# GLOBAL INSTANCE AND CONVENIENCE FUNCTIONS
# ============================================================================

_global_analytics: Optional[ToolAnalytics] = None


def get_analytics(project_root: Optional[Path] = None) -> ToolAnalytics:
    """
    Get global ToolAnalytics instance.
    
    Args:
        project_root: Project root directory. Uses cached instance if same root.
        
    Returns:
        ToolAnalytics instance.
    """
    global _global_analytics
    
    if _global_analytics is None or (
        project_root and _global_analytics._project_root != project_root
    ):
        _global_analytics = ToolAnalytics(project_root)
    
    return _global_analytics


def log_tool_usage(
    tool_name: str,
    success: bool,
    duration_ms: int,
    error: Optional[str] = None,
    project_root: Optional[Path] = None
) -> None:
    """
    Convenience function to log tool usage.
    
    Args:
        tool_name: Name of the tool that was executed.
        success: Whether the execution succeeded.
        duration_ms: Execution duration in milliseconds.
        error: Error message if failed (optional).
        project_root: Project root directory (optional).
    """
    analytics = get_analytics(project_root)
    analytics.log_tool_usage(tool_name, success, duration_ms, error)


def get_analytics_summary(project_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Convenience function to get analytics summary.
    
    Args:
        project_root: Project root directory (optional).
        
    Returns:
        Analytics summary dict.
    """
    analytics = get_analytics(project_root)
    return analytics.get_summary()


def reset_analytics(project_root: Optional[Path] = None) -> None:
    """
    Convenience function to reset analytics.
    
    Args:
        project_root: Project root directory (optional).
    """
    analytics = get_analytics(project_root)
    analytics.reset()


__all__ = [
    "ToolAnalytics",
    "get_analytics",
    "log_tool_usage",
    "get_analytics_summary",
    "reset_analytics",
]
