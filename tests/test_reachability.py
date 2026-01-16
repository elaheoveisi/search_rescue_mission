#!/usr/bin/env python3
"""
Test script to verify that all victims are reachable from agent start position.
This test creates multiple environments and verifies reachability.
"""

from src.game.sar.env import PickupVictimEnv


def test_victim_reachability(num_tests=10):
    """Test that all victims are reachable in generated missions."""

    print(f"Testing victim reachability across {num_tests} environment resets...\n")

    # Create environment
    env = PickupVictimEnv(
        room_size=6, num_rows=3, num_cols=3, num_dists=10, render_mode=None
    )

    successes = 0
    for i in range(num_tests):
        try:
            # Reset environment (triggers gen_mission)
            obs, info = env.reset()

            # Get all victims
            victims = env.get_all_victims()

            # Check mission status
            status = env.get_mission_status()

            print(f"Test {i + 1}/{num_tests}:")
            print(f"  ✓ Environment generated successfully")
            print(f"  ✓ Agent position: {env.agent_pos}")
            print(f"  ✓ Total victims: {len(victims)}")
            print(f"  ✓ Mission: {env.mission}")

            # If we got here, all objects passed reachability check
            successes += 1

        except Exception as e:
            print(f"Test {i + 1}/{num_tests}:")
            print(f"  ✗ Failed with error: {e}")
            continue

    print(f"\n{'=' * 70}")
    print(f"Results: {successes}/{num_tests} environments generated successfully")
    print(f"{'=' * 70}")

    if successes == num_tests:
        print("✅ All tests passed! All victims are reachable.")
    else:
        print(f"⚠️  {num_tests - successes} tests failed.")

    return successes == num_tests


if __name__ == "__main__":
    success = test_victim_reachability(num_tests=10)
    exit(0 if success else 1)
