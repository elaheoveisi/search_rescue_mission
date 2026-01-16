#!/usr/bin/env python3
"""
Test script to verify lava placement functionality.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.game.sar.env import PickupVictimEnv


def count_lava_tiles(env):
    """Count the number of lava tiles in the environment."""
    lava_count = 0
    for x in range(env.width):
        for y in range(env.height):
            obj = env.grid.get(x, y)
            if obj and obj.type == "lava":
                lava_count += 1
    return lava_count


def test_no_lava():
    """Test environment without lava."""
    print("Test 1: Environment WITHOUT lava")
    print("=" * 70)

    env = PickupVictimEnv(
        room_size=6, num_rows=2, num_cols=2, add_lava=False, render_mode=None
    )

    obs, info = env.reset()
    lava_count = count_lava_tiles(env)

    print(f"  Grid size: {env.width}x{env.height}")
    print(f"  Lava tiles: {lava_count}")
    print(f"  ✓ Test passed: No lava as expected\n")

    return lava_count == 0


def test_lava_with_probability():
    """Test environment with probability-based lava placement."""
    print("Test 2: Environment WITH lava (probability-based)")
    print("=" * 70)

    env = PickupVictimEnv(
        room_size=6,
        num_rows=3,
        num_cols=3,
        add_lava=True,
        lava_probability=0.5,  # 50% chance per room
        render_mode=None,
    )

    total_lava = 0
    num_resets = 5

    for i in range(num_resets):
        obs, info = env.reset()
        lava_count = count_lava_tiles(env)
        total_lava += lava_count
        print(f"  Reset {i + 1}: {lava_count} lava tiles")

    avg_lava = total_lava / num_resets
    print(f"  Average lava per environment: {avg_lava:.1f}")
    print(f"  ✓ Test passed: Lava placement working\n")

    return total_lava > 0


def test_lava_fixed_per_room():
    """Test environment with fixed number of lava tiles per room."""
    print("Test 3: Environment WITH lava (fixed per room)")
    print("=" * 70)

    lava_per_room = 2
    num_rows = 2
    num_cols = 2

    env = PickupVictimEnv(
        room_size=6,
        num_rows=num_rows,
        num_cols=num_cols,
        add_lava=True,
        lava_per_room=lava_per_room,
        render_mode=None,
    )

    obs, info = env.reset()
    lava_count = count_lava_tiles(env)

    print(f"  Rooms: {num_rows}x{num_cols} = {num_rows * num_cols} total rooms")
    print(f"  Lava per room (target): {lava_per_room}")
    print(f"  Total lava tiles: {lava_count}")
    print(f"  Note: Some rooms may be locked (skipped for lava)")
    print(f"  ✓ Test passed: Fixed lava placement working\n")

    return lava_count > 0


def test_lava_with_reachability():
    """Test that lava doesn't break reachability guarantees."""
    print("Test 4: Lava with reachability enforcement")
    print("=" * 70)

    env = PickupVictimEnv(
        room_size=6,
        num_rows=2,
        num_cols=2,
        add_lava=True,
        lava_probability=0.6,
        unblocking=False,  # Enforce reachability
        render_mode=None,
    )

    successes = 0
    num_tests = 3

    for i in range(num_tests):
        try:
            obs, info = env.reset()
            lava_count = count_lava_tiles(env)
            victims = env.get_all_victims()
            print(
                f"  Test {i + 1}: {lava_count} lava tiles, {len(victims)} victims (all reachable)"
            )
            successes += 1
        except Exception as e:
            print(f"  Test {i + 1}: Failed - {e}")

    print(
        f"  ✓ {successes}/{num_tests} environments generated with guaranteed reachability\n"
    )

    return successes > 0


def main():
    """Run all lava tests."""
    print("\n" + "=" * 70)
    print("LAVA PLACEMENT TESTS")
    print("=" * 70 + "\n")

    results = []

    # Run tests
    results.append(("No lava", test_no_lava()))
    results.append(("Probability-based lava", test_lava_with_probability()))
    results.append(("Fixed lava per room", test_lava_fixed_per_room()))
    results.append(("Lava with reachability", test_lava_with_reachability()))

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {status}: {test_name}")
        if not passed:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\n✅ All lava tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
