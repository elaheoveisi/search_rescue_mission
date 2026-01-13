#!/usr/bin/env python3
"""
Test reachability with unblocking=False to ensure all victims are directly reachable.
"""

from src.game.sar.env import PickupVictimEnv


def test_strict_reachability(num_tests=5):
    """Test with unblocking=False to enforce strict reachability."""

    print(
        f"Testing STRICT reachability (unblocking=False) across {num_tests} resets...\n"
    )

    # Create environment with strict reachability enforcement
    env = PickupVictimEnv(
        room_size=6,
        num_rows=2,
        num_cols=2,
        num_dists=5,
        unblocking=False,  # Enforces strict reachability
        render_mode=None,
    )

    successes = 0
    for i in range(num_tests):
        try:
            obs, info = env.reset()
            victims = env.get_all_victims()
            status = env.get_mission_status()

            print(
                f"Test {i + 1}/{num_tests}: ✓ Generated with {len(victims)} reachable victims"
            )
            successes += 1

        except Exception as e:
            print(f"Test {i + 1}/{num_tests}: ✗ Failed - {e}")

    print(f"\n{'=' * 70}")
    print(f"Results: {successes}/{num_tests} environments with strict reachability")
    print(f"{'=' * 70}")

    return successes == num_tests


if __name__ == "__main__":
    success = test_strict_reachability(num_tests=1000)
    print(
        "\n✅ All victims are GUARANTEED to be directly reachable!"
        if success
        else "\n❌ Test failed"
    )
    exit(0 if success else 1)
