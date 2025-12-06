"""
SQLite Database Layer for Pulse IDE.

Manages chat session history and persistence using SQLite.
Provides methods for creating sessions, saving messages, and retrieving history.
"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from contextlib import contextmanager

from src.core.config import Config


class DatabaseManager:
    """
    Manages SQLite database operations for chat history.

    Handles session creation, message persistence, and history retrieval.
    Uses idempotent schema creation for safe initialization.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the DatabaseManager.

        Args:
            db_path: Path to SQLite database file. Defaults to Config.DB_PATH.
        """
        self.db_path = db_path or Config.DB_PATH

        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize schema
        self._init_schema()

    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.

        Yields:
            sqlite3.Connection: Database connection with row factory.
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """
        Initialize database schema (idempotent).

        Creates tables if they don't exist:
        - chat_sessions: Stores session metadata
        - chat_messages: Stores individual messages
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create chat_sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create chat_messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
                )
            """)

            # Create index for faster message retrieval
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session_id
                ON chat_messages(session_id)
            """)

            conn.commit()

    def create_session(self, title: str = "New Chat") -> str:
        """
        Create a new chat session.

        Args:
            title: Title for the new session. Defaults to "New Chat".

        Returns:
            str: Unique session ID (UUID).
        """
        session_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO chat_sessions (id, title, created_at)
                VALUES (?, ?, ?)
                """,
                (session_id, title, created_at)
            )

        return session_id

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> int:
        """
        Save a message to a chat session.

        Args:
            session_id: ID of the session to add message to.
            role: Message role (e.g., "user", "assistant", "system").
            content: Message content.

        Returns:
            int: ID of the inserted message.
        """
        timestamp = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO chat_messages (session_id, role, content, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, role, content, timestamp)
            )
            message_id = cursor.lastrowid

        return message_id

    def get_session_history(self, session_id: str) -> List[Dict]:
        """
        Retrieve all messages for a session, ordered by timestamp.

        Args:
            session_id: ID of the session to retrieve.

        Returns:
            List[Dict]: List of messages with keys: id, role, content, timestamp.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, session_id, role, content, timestamp
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY timestamp ASC
                """,
                (session_id,)
            )

            messages = []
            for row in cursor.fetchall():
                messages.append({
                    "id": row["id"],
                    "session_id": row["session_id"],
                    "role": row["role"],
                    "content": row["content"],
                    "timestamp": row["timestamp"]
                })

        return messages

    def get_all_sessions(self) -> List[Dict]:
        """
        Retrieve all chat sessions, ordered by creation date (newest first).

        Returns:
            List[Dict]: List of sessions with keys: id, title, created_at.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, title, created_at
                FROM chat_sessions
                ORDER BY created_at DESC
                """
            )

            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    "id": row["id"],
                    "title": row["title"],
                    "created_at": row["created_at"]
                })

        return sessions

    def delete_session(self, session_id: str) -> None:
        """
        Delete a session and all its messages.

        Args:
            session_id: ID of the session to delete.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Delete messages first (foreign key constraint)
            cursor.execute(
                "DELETE FROM chat_messages WHERE session_id = ?",
                (session_id,)
            )

            # Delete session
            cursor.execute(
                "DELETE FROM chat_sessions WHERE id = ?",
                (session_id,)
            )

    def update_session_title(self, session_id: str, new_title: str) -> None:
        """
        Update the title of a session.

        Args:
            session_id: ID of the session to update.
            new_title: New title for the session.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE chat_sessions
                SET title = ?
                WHERE id = ?
                """,
                (new_title, session_id)
            )


# Singleton instance for easy access
_db_instance: Optional[DatabaseManager] = None


def get_db() -> DatabaseManager:
    """
    Get the singleton DatabaseManager instance.

    Returns:
        DatabaseManager: Singleton database manager instance.
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
