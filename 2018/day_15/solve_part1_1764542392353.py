import sys
from collections import deque

class Unit:
    def __init__(self, y, x, u_type):
        self.y = y
        self.x = x
        self.type = u_type
        self.hp = 200
        self.attack_power = 3
        self.id = f"{u_type}_{y}_{x}" # Unique ID for debugging

    def __repr__(self):
        return f"{self.type}({self.hp}) at ({self.y}, {self.x})"

def solve():
    with open("input.txt") as f:
        lines = [line.rstrip() for line in f]

    height = len(lines)
    width = len(lines[0])
    
    grid = []
    units = []
    
    for r, line in enumerate(lines):
        row = []
        for c, char in enumerate(line):
            if char in 'GE':
                units.append(Unit(r, c, char))
                row.append('.') # Unit stands on open ground
            else:
                row.append(char)
        grid.append(row)

    def get_reading_order_neighbors(y, x):
        # Up, Left, Right, Down
        candidates = [(y-1, x), (y, x-1), (y, x+1), (y+1, x)]
        return [
            (ny, nx) for ny, nx in candidates
            if 0 <= ny < height and 0 <= nx < width
        ]

    def is_free(y, x, current_units):
        if grid[y][x] == '#': return False
        for u in current_units:
            if u.hp > 0 and u.y == y and u.x == x:
                return False
        return True

    # BFS to find distances from a start point to all reachable points
    # Returns a dict: (y, x) -> distance
    def bfs(start_y, start_x, current_units):
        q = deque([(start_y, start_x, 0)])
        visited = {}
        visited[(start_y, start_x)] = 0
        
        # Build set of occupied positions for fast lookup
        occupied = set()
        for u in current_units:
            if u.hp > 0:
                occupied.add((u.y, u.x))
        
        while q:
            y, x, dist = q.popleft()
            
            for ny, nx in get_reading_order_neighbors(y, x):
                if grid[ny][nx] == '#' or (ny, nx) in occupied:
                    continue
                if (ny, nx) not in visited:
                    visited[(ny, nx)] = dist + 1
                    q.append((ny, nx, dist + 1))
        return visited

    rounds = 0
    while True:
        # Sort units by reading order
        units.sort(key=lambda u: (u.y, u.x))
        
        # We iterate over a copy or by index, but need to handle deaths immediately
        # Using a list and skipping dead ones is safest.
        # But dead units should not block movement.
        # Logic: Iterate through sorted list. If unit is dead, skip.
        
        combat_ended = False
        
        for i, unit in enumerate(units):
            if unit.hp <= 0:
                continue
            
            # Identify targets
            targets = [u for u in units if u.hp > 0 and u.type != unit.type]
            if not targets:
                combat_ended = True
                break
                
            # --- MOVE PHASE ---
            
            # Check if already in range
            in_range = False
            for t in targets:
                if abs(unit.y - t.y) + abs(unit.x - t.x) == 1:
                    in_range = True
                    break
            
            if not in_range:
                # Find all open squares in range of targets
                target_squares = set()
                occupied = set((u.y, u.x) for u in units if u.hp > 0)
                
                for t in targets:
                    for ny, nx in get_reading_order_neighbors(t.y, t.x):
                        if grid[ny][nx] != '#' and (ny, nx) not in occupied:
                            target_squares.add((ny, nx))
                
                if target_squares:
                    # BFS from unit to find reachable target squares
                    dists = bfs(unit.y, unit.x, units)
                    
                    reachable_squares = []
                    for (ty, tx) in target_squares:
                        if (ty, tx) in dists:
                            reachable_squares.append((dists[(ty, tx)], ty, tx))
                    
                    if reachable_squares:
                        # Choose target: min dist, then reading order
                        reachable_squares.sort()
                        chosen_dist, chosen_y, chosen_x = reachable_squares[0]
                        
                        # Choose step: BFS from chosen target back to unit
                        # Actually we can use the same BFS logic but starting from chosen target
                        # ignoring the unit itself as an obstacle
                        
                        # We need to find which neighbor of unit leads to chosen_target with chosen_dist - 1
                        
                        # Re-run BFS from chosen target to find distances to everything
                        # This BFS treats the unit's current position as empty (it is)
                        # but other units as obstacles.
                        # Wait, the unit is moving, so it shouldn't block itself.
                        # But other units block.
                        
                        # Correct approach:
                        # BFS from chosen_target.
                        # Check unit's neighbors.
                        # Pick neighbor with dist == chosen_dist - 1.
                        # Tie break neighbors by reading order.
                        
                        # Temporarily remove unit from occupied checks? 
                        # No, the `bfs` function takes `current_units`. 
                        # The unit itself is in `current_units`, so it would be treated as obstacle.
                        # We should pass a list without current unit to BFS?
                        # Actually, BFS is finding paths *to* the target.
                        # The target is an empty square.
                        # We are finding path *from* target *to* unit neighbors.
                        # The unit's current position is where we want to reach (sort of).
                        # Effectively, we want to know dist from target to each of unit's neighbors.
                        
                        # Let's modify bfs to accept an exclusion list or just handle it.
                        # A cleaner way: 
                        # BFS from unit is sufficient to find distances to targets.
                        # But to find the *first step*, we need to know which neighbor is on the optimal path.
                        # There might be multiple optimal paths.
                        # We need the neighbor that starts a path.
                        # The rule: "If multiple steps would put the unit equally closer to its destination, the unit chooses the step which is first in reading order."
                        
                        # So, check each neighbor N of unit.
                        # If N is valid (not wall, not occupied), calculate dist(N, chosen_target).
                        # We want min(dist(N, chosen_target)).
                        # Break ties with N's reading order.
                        
                        # To get dist(N, chosen_target), we can:
                        # 1. BFS from N for each N. (Slow? 4 BFS per move)
                        # 2. BFS from chosen_target once. (1 BFS per move). Better.
                        
                        # For the reverse BFS, we treat all units as obstacles EXCEPT the current unit (obviously, since we move from it).
                        # And we treat the chosen_target as start.
                        
                        # Let's define a special BFS for this.
                        back_dists = bfs(chosen_y, chosen_x, [u for u in units if u != unit])
                        
                        best_step = None
                        min_step_dist = float('inf')
                        
                        # Check neighbors in reading order
                        for ny, nx in get_reading_order_neighbors(unit.y, unit.x):
                            if (ny, nx) in back_dists:
                                d = back_dists[(ny, nx)]
                                if d < min_step_dist:
                                    min_step_dist = d
                                    best_step = (ny, nx)
                        
                        if best_step:
                            unit.y, unit.x = best_step

            # --- ATTACK PHASE ---
            # Check adjacent enemies
            adjacent_enemies = []
            for t in targets:
                if abs(unit.y - t.y) + abs(unit.x - t.x) == 1:
                    adjacent_enemies.append(t)
            
            if adjacent_enemies:
                # Select enemy: lowest HP, then reading order
                adjacent_enemies.sort(key=lambda u: (u.hp, u.y, u.x))
                target = adjacent_enemies[0]
                
                target.hp -= unit.attack_power
                if target.hp <= 0:
                    # Don't remove from list immediately to not mess up loop index?
                    # We are iterating by index `i`. If we remove something, indices shift.
                    # We shouldn't remove from `units` list during iteration.
                    # We just mark it as dead (hp <= 0).
                    # Dead units are skipped in the loop (checked at start).
                    # Also dead units are not obstacles (checked in `bfs`).
                    pass

        if combat_ended:
            total_hp = sum(u.hp for u in units if u.hp > 0)
            print(f"Combat ended after {rounds} full rounds.")
            print(f"Total HP: {total_hp}")
            print(f"Answer: {rounds * total_hp}")
            break
            
        rounds += 1
        # Cleanup dead units to keep list clean (optional, but good for performance)
        units = [u for u in units if u.hp > 0]

solve()
