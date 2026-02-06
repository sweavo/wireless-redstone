#!/bin/env python3
"""Wireless Redstone Calculator

By using repeaters and comparators, we can have redstone signals arrive in the same tick as one another, but with a known position in the block update order.

This means we can control the sequence in which entities are created within a given tick.

Since entities check for falling on a rota of four ticks, then entities created in the same tick will fall on different ticks, depending on the order in which they were created.

This calculator takes a list of comparators and repeaters, and calculates the order in which entities will be created, and the tick on which they will fall.

Usage:
    python wireless-redstone-calculator.py

    It reads the input from stdin, and outputs the result to stdout.

Input format:
    Each line of input represents a chain of repeaters and comparators, and has the following format:

    `((R(0-9))|C)+`

    Where R represents a repeater, C represents a comparator, and the number represents the delay of the repeater.

Output format:
    The output is the sequence in which the block at the end of the channel will be updated, where A is the first line, B is the second line, and so on. The output is in the format:
    A,B,C,...

Design:

Since the algorithm centers on the order in which redstone updates are queued, the center of the design is a dict of queues of redstone updates, where the key is the tick on which the update will occur, and the value is a list of updates that will occur on that tick. Each update is represented as a tuple of (line-name, tail), where line-name is the assigned letter (A, B, C, etc.) for the input line, and tail is the remaining portion of the line that has not yet been processed.

During input, each line is assigned a line-name (A for the first line, B for the second, C for the third, and so on). It starts by queueing the full line for each line-name in the queue for tick 0. Then, it processes the queue for each tick, and for each update, it consumes the first element (Rn or C) from the tail, calculates the next update that will occur as a result of the current element, and queues the updated tuple with the remaining tail for the appropriate future tick. Then the next tick in order is processed, and so on, until there are no more updates to process. When processing the updates for a tick, they are processed in the order they were queued, which ensures that the order of updates is correct.

During operation, it's possible that some lines are missing updates in a given tick, but the final tick must contain all the input line-names, and each line-name must have an empty tail, as the purpose of this redstone technique is to have all the lines fully processed in the same tick with a specific subtick order. If the final tick does not contain all the input line-names or if any line-name has a non-empty tail, then a warning is printed to stderr, and the internal tick map is written to stdout for debugging purposes.


"""
import re

RE_ELEMENT = re.compile(r'^(R[0-3]]|C)')

if __name__ == "__main__":
    import sys

    # Read input lines and assign line-names
    lines = [line.strip() for line in sys.stdin if line.strip()]
    line_names = [chr(ord('A') + i) for i in range(len(lines))]

    # Initialize the tick map
    tick_map = {}

    # Queue the initial updates for each line
    for line_name, line in zip(line_names, lines):
        tick_map.setdefault(0, []).append((line_name, line))

    # Process the tick map
    more_to_process = True
    while more_to_process:
        more_to_process = False
        current_tick = min(tick_map.keys())
        updates = tick_map.pop(current_tick)

        for line_name, tail in updates:
            if not tail:
                continue  # No more elements to process

            m = RE_ELEMENT.match(tail)
            if not m:
                print(f"Warning: Invalid element in line '{line_name}' at tick {current_tick}: {tail}", file=sys.stderr)
                continue
            element = m.group(1)
            remaining_tail = tail[len(element):]
            if remaining_tail:
                more_to_process = True

            if element.startswith('R'):
                delay = int(element[1])
                next_tick = current_tick + (1+delay) * 2
                tick_map.setdefault(next_tick, []).append((line_name, remaining_tail))
            elif element.startswith('C'):
                next_tick = current_tick + 2
                tick_map.setdefault(next_tick, []).append((line_name, remaining_tail))
            else:
                print(f"Warning: Invalid element '{element}' in line '{line_name}'", file=sys.stderr)

    # Check final state of the tick map
    final_tick = max(tick_map.keys()) if tick_map else 0
    final_updates = tick_map.get(final_tick, [])

    if len(final_updates) != len(line_names) or any(tail for _, tail in final_updates):
        print("Warning: Final tick does not contain all line-names or has non-empty tails.", file=sys.stderr)
        print("Final tick map:", file=sys.stderr)
        for tick, updates in sorted(tick_map.items()):
            print(f"Tick {tick}: {updates}", file=sys.stderr)
    else:
        # Output the order of line-names in the final tick
        output_order = [line_name for line_name, _ in final_updates]
        print(",".join(output_order))