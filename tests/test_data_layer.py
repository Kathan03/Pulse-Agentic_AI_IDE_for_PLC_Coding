"""
Test script for data layer components.

Tests Configuration, Database, and RAG engines.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import config
from src.core.db import DatabaseManager
from src.core.chroma_db_rag import ChromaDBRAG


def test_config():
    """Test configuration loading."""
    print("=" * 60)
    print("TESTING CONFIGURATION")
    print("=" * 60)

    try:
        print(f"[OK] OpenAI Model: {config.OPENAI_MODEL_NAME}")
        print(f"[OK] OpenAI API Key Set: {bool(config.OPENAI_API_KEY)}")
        print(f"[OK] DB Path: {config.DB_PATH}")
        print(f"[OK] Chroma DB Path: {config.CHROMA_DB_PATH}")

        # Test validation
        config.Config.validate()
        print("[OK] Configuration validation passed")

        # Get summary
        summary = config.Config.get_summary()
        print(f"[OK] Configuration Summary: {summary}")

        print("\n[PASS] Configuration test PASSED\n")
        return True

    except Exception as e:
        print(f"\n[FAIL] Configuration test FAILED: {e}\n")
        return False


def test_database():
    """Test database operations."""
    print("=" * 60)
    print("TESTING DATABASE")
    print("=" * 60)

    try:
        # Create a test database in a temporary location
        test_db_path = Path(__file__).parent.parent / "data" / "test_pulse.db"
        db = DatabaseManager(db_path=test_db_path)

        # Test 1: Create a session
        session_id = db.create_session("Test Session")
        print(f"[OK] Created session: {session_id}")

        # Test 2: Save messages
        msg_id_1 = db.save_message(session_id, "user", "Hello, Pulse!")
        print(f"[OK] Saved user message: {msg_id_1}")

        msg_id_2 = db.save_message(session_id, "assistant", "Hello! How can I help?")
        print(f"[OK] Saved assistant message: {msg_id_2}")

        # Test 3: Retrieve history
        history = db.get_session_history(session_id)
        print(f"[OK] Retrieved {len(history)} messages:")
        for msg in history:
            print(f"  - [{msg['role']}]: {msg['content'][:50]}...")

        # Test 4: Get all sessions
        sessions = db.get_all_sessions()
        print(f"[OK] Found {len(sessions)} total sessions")

        # Test 5: Update session title
        db.update_session_title(session_id, "Updated Test Session")
        print("[OK] Updated session title")

        # Cleanup: Delete test session
        db.delete_session(session_id)
        print("[OK] Cleaned up test session")

        # Cleanup: Remove test database
        if test_db_path.exists():
            test_db_path.unlink()
            print("[OK] Removed test database file")

        print("\n[PASS] Database test PASSED\n")
        return True

    except Exception as e:
        print(f"\n[FAIL] Database test FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_rag():
    """Test RAG engine."""
    print("=" * 60)
    print("TESTING RAG ENGINE")
    print("=" * 60)

    try:
        # Create a test RAG instance
        test_chroma_path = Path(__file__).parent.parent / "data" / "test_chroma_db"
        rag = ChromaDBRAG(chroma_db_path=test_chroma_path)

        # Clear any existing data
        rag.clear_collection()
        print("[OK] Cleared test collection")

        # Test 1: Get initial stats
        stats = rag.get_collection_stats()
        print(f"[OK] Initial collection stats: {stats}")

        # Test 2: Ingest codebase (current project)
        project_root = Path(__file__).parent.parent
        print(f"[OK] Ingesting codebase from: {project_root}")

        ingest_stats = rag.ingest_codebase(project_root)
        print(f"[OK] Ingestion complete:")
        print(f"  - Files processed: {ingest_stats['files_processed']}")
        print(f"  - Chunks created: {ingest_stats['chunks_created']}")

        # Test 3: Get updated stats
        stats = rag.get_collection_stats()
        print(f"[OK] Updated collection stats: {stats}")

        # Test 4: Search for "main function"
        results = rag.search_codebase("main function", n_results=3)
        print(f"[OK] Search results for 'main function' ({len(results)} results):")
        for i, result in enumerate(results, 1):
            print(f"\n  Result {i}:")
            print(f"    Path: {result['metadata'].get('path', 'N/A')}")
            print(f"    Chunk: {result['metadata'].get('chunk_index', 'N/A')}")
            print(f"    Distance: {result.get('distance', 'N/A'):.4f}")
            print(f"    Content preview: {result['content'][:100]}...")

        # Test 5: Search for "configuration"
        results = rag.search_codebase("configuration management", n_results=2)
        print(f"\n[OK] Search results for 'configuration management' ({len(results)} results):")
        for i, result in enumerate(results, 1):
            print(f"  - {result['metadata'].get('path', 'N/A')}")

        # Cleanup: Clear and remove test ChromaDB
        rag.clear_collection()
        print("\n[OK] Cleaned up test collection")

        # Remove test directory (best effort - Windows may lock files)
        import shutil
        import time
        if test_chroma_path.exists():
            try:
                # Try to close any open connections
                del rag
                time.sleep(0.5)  # Brief delay to allow file handles to release
                shutil.rmtree(test_chroma_path)
                print("[OK] Removed test ChromaDB directory")
            except PermissionError:
                print("[WARNING] Could not remove test directory (Windows file lock)")
                print("           This is normal on Windows and won't affect functionality")

        print("\n[PASS] RAG test PASSED\n")
        return True

    except Exception as e:
        print(f"\n[FAIL] RAG test FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("DATA LAYER VERIFICATION TEST SUITE")
    print("=" * 60 + "\n")

    results = {
        "Configuration": test_config(),
        "Database": test_database(),
        "RAG Engine": test_rag()
    }

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results.items():
        status = "[PASSED]" if passed else "[FAILED]"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n[SUCCESS] ALL TESTS PASSED! Data layer is ready.\n")
        return 0
    else:
        print("\n[WARNING] SOME TESTS FAILED. Please check the errors above.\n")
        return 1


if __name__ == "__main__":
    exit(main())
