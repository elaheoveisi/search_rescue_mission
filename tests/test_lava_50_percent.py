#!/usr/bin/env python3
"""
Test script to verify lava is placed in approximately 50% of rooms.
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


def count_rooms_with_lava(env):
    """Count how many rooms have at least one lava tile."""
    rooms_with_lava = set()

    for x in range(env.width):
        for y in range(env.height):
            obj = env.grid.get(x, y)
            if obj and obj.type == "lava":
                # Find which room this lava is in
                room = env.room_from_pos(x, y)
                if room:
                    rooms_with_lava.add((room.top[0], room.top[1]))

    return len(rooms_with_lava)


def main():
    """Test lava placement at 50% probability."""
    print("=" * 70)
    print("Testing Lava Placement (50% of rooms)")
    print("=" * 70 + "\n")

    num_rows = 3
    num_cols = 3
    total_rooms = num_rows * num_cols
    num_tests = 10

    env = PickupVictimEnv(
        room_size=6,
        num_rows=num_rows,
        num_cols=num_cols,
        add_lava=True,  # Default is now True
        lava_probability=0.5,  # Default is now 0.5
        render_mode=None,
    )

    total_rooms_with_lava = 0
    total_lava_tiles = 0

    print(f"Environment: {num_rows}x{num_cols} = {total_rooms} rooms")
    print(f"Expected: ~{total_rooms * 0.5:.1f} rooms with lava (50%)")
    print(f"Running {num_tests} tests...\n")

    for i in range(num_tests):
        obs, info = env.reset()

        lava_tiles = count_lava_tiles(env)
        rooms_with_lava = count_rooms_with_lava(env)

        total_lava_tiles += lava_tiles
        total_rooms_with_lava += rooms_with_lava

        percentage = (rooms_with_lava / total_rooms) * 100
        print(
            f"Test {i + 1:2d}: {rooms_with_lava}/{total_rooms} rooms with lava ({percentage:.0f}%) - {lava_tiles} tiles total"
        )

    avg_rooms_with_lava = total_rooms_with_lava / num_tests
    avg_lava_tiles = total_lava_tiles / num_tests
    avg_percentage = (avg_rooms_with_lava / total_rooms) * 100

    print("\n" + "=" * 70)
    print("Results")
    print("=" * 70)
    print(
        f"Average rooms with lava: {avg_rooms_with_lava:.1f}/{total_rooms} ({avg_percentage:.1f}%)"
    )
    print(f"Average lava tiles: {avg_lava_tiles:.1f}")
    print(f"Expected percentage: 50%")
    print(f"Actual percentage: {avg_percentage:.1f}%")

    # Success if within reasonable range (30-70% due to randomness)
    if 30 <= avg_percentage <= 70:
        print("\n✅ Test PASSED: Lava placement is within expected range!")
        return 0
    else:
        print(
            f"\n❌ Test FAILED: Lava percentage {avg_percentage:.1f}% is outside expected range (30-70%)"
        )
        return 1


if __name__ == "__main__":
    exit(main())
