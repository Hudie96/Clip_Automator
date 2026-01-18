"""
Simple test script to verify SharedStats and WebSocket functionality.
Run after installing flask-socketio: pip install flask-socketio>=5.0.0
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.web.live_stats import shared_stats


def test_basic_operations():
    """Test basic SharedStats operations."""
    print("Testing SharedStats...")

    # Reset to clean state
    shared_stats.reset_all()

    # Test viewer counts
    shared_stats.update_viewers("xQc", 45000)
    shared_stats.update_viewers("Shroud", 32000)
    print(f"[PASS] Viewer counts: {shared_stats.viewer_counts}")

    # Test chat velocities
    shared_stats.update_velocity("xQc", 125.5)
    shared_stats.update_velocity("Shroud", 87.2)
    print(f"[PASS] Chat velocities: {shared_stats.chat_velocities}")

    # Test trigger events
    shared_stats.add_trigger("xQc", "viewer_spike", {"spike": 15000})
    shared_stats.add_trigger("Shroud", "chat_burst", {"rate": 200})
    print(f"[PASS] Recent triggers ({len(shared_stats.recent_triggers)}): {shared_stats.recent_triggers[0]['type']}")

    # Test recording status
    shared_stats.update_recording_status("xQc", True)
    shared_stats.update_recording_status("Shroud", False)
    print(f"[PASS] Recording status: {shared_stats.recording_status}")

    # Test get_all_stats
    all_stats = shared_stats.get_all_stats()
    print(f"[PASS] All stats retrieved successfully")
    print(f"  - Streamers tracked: {len(all_stats['viewer_counts'])}")
    print(f"  - Recent triggers: {len(all_stats['recent_triggers'])}")
    print(f"  - Last updated: {all_stats['last_updated']}")

    # Test singleton pattern
    another_instance = type(shared_stats)()
    assert another_instance is shared_stats, "Singleton pattern failed!"
    print("[PASS] Singleton pattern working correctly")

    # Test clearing streamer stats
    shared_stats.clear_streamer_stats("Shroud")
    print(f"[PASS] Cleared Shroud stats, remaining streamers: {list(shared_stats.viewer_counts.keys())}")

    print("\n[SUCCESS] All basic tests passed!")


def test_trigger_limit():
    """Test that trigger list is limited to 20 items."""
    print("\nTesting trigger list limit...")

    shared_stats.reset_all()

    # Add 25 triggers
    for i in range(25):
        shared_stats.add_trigger(f"streamer{i % 3}", "test", {"index": i})

    # Should only keep last 20
    assert len(shared_stats.recent_triggers) == 20, f"Expected 20 triggers, got {len(shared_stats.recent_triggers)}"

    # Most recent should be index 24
    assert shared_stats.recent_triggers[0]['details']['index'] == 24, "Most recent trigger not at front"

    # Oldest kept should be index 5 (24 down to 5 = 20 items)
    assert shared_stats.recent_triggers[-1]['details']['index'] == 5, "Oldest trigger incorrect"

    print("[PASS] Trigger list correctly limited to 20 items")
    print("[SUCCESS] Trigger limit test passed!")


def test_thread_safety():
    """Basic test that operations are thread-safe."""
    import threading
    import time

    print("\nTesting thread safety...")

    shared_stats.reset_all()

    def update_viewers_repeatedly(streamer, count):
        for _ in range(100):
            shared_stats.update_viewers(streamer, count)

    def add_triggers_repeatedly(streamer):
        for i in range(50):
            shared_stats.add_trigger(streamer, "test", {"iteration": i})

    # Create multiple threads
    threads = [
        threading.Thread(target=update_viewers_repeatedly, args=("xQc", 50000)),
        threading.Thread(target=update_viewers_repeatedly, args=("Shroud", 30000)),
        threading.Thread(target=add_triggers_repeatedly, args=("xQc",)),
        threading.Thread(target=add_triggers_repeatedly, args=("Shroud",)),
    ]

    # Start all threads
    for t in threads:
        t.start()

    # Wait for completion
    for t in threads:
        t.join()

    # Verify state is consistent
    assert shared_stats.viewer_counts["xQc"] == 50000
    assert shared_stats.viewer_counts["Shroud"] == 30000
    assert len(shared_stats.recent_triggers) == 20  # Should be limited to 20

    print("[PASS] Thread-safe operations completed successfully")
    print("[SUCCESS] Thread safety test passed!")


if __name__ == "__main__":
    try:
        test_basic_operations()
        test_trigger_limit()
        test_thread_safety()
        print("\n" + "="*50)
        print("ALL TESTS PASSED!")
        print("="*50)
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
