import sys
from collections import deque

class Unit:
    def __init__(self, y, x, u_type, attack_power):
        self.y = y
        self.x = x
        self.type = u_type
        self.hp = 200
        self.attack_power = attack_power
        self.id = f"{u_type}_{y}_{x}" 

    def __repr__(self):
        return f"{self.type}({self.hp})"

def run_simulation(elf_attack_power, lines):
    height = len(lines)
    width = len(lines[0])
    
    grid = []
    units = []
    
    elves_count = 0
    
    for r, line in enumerate(lines):
        row = []
        for c, char in enumerate(line):
            if char in 'GE':
                ap = elf_attack_power if char == 'E' else 3
                u = Unit(r, c, char, ap)
                units.append(u)
                if char == 'E':
                    elves_count += 1
                row.append('.') 
            else:
                row.append(char)
        grid.append(row)

    def get_reading_order_neighbors(y, x):
        candidates = [(y-1, x), (y, x-1), (y, x+1), (y+1, x)]
        return [
            (ny, nx) for ny, nx in candidates
            if 0 <= ny < height and 0 <= nx < width
        ]

    def bfs(start_y, start_x, current_units, target_squares=None):
        q = deque([(start_y, start_x, 0)])
        visited = {} # (y, x) -> dist
        visited[(start_y, start_x)] = 0
        
        occupied = set()
        for u in current_units:
            if u.hp > 0:
                occupied.add((u.y, u.x))
        
        # Optimization: If we have target_squares, we can stop when we found all reachable ones?
        # BFS layer by layer logic ensures we find min distances.
        # But we need to explore the whole component to find *all* reachable targets 
        # to sort them.
        
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
        units.sort(key=lambda u: (u.y, u.x))
        
        combat_ended = False
        
        for i, unit in enumerate(units):
            if unit.hp <= 0:
                continue
            
            targets = [u for u in units if u.hp > 0 and u.type != unit.type]
            if not targets:
                combat_ended = True
                break
                
            # --- MOVE PHASE ---
            in_range = False
            for t in targets:
                if abs(unit.y - t.y) + abs(unit.x - t.x) == 1:
                    in_range = True
                    break
            
            if not in_range:
                target_squares = set()
                occupied_list = [(u.y, u.x) for u in units if u.hp > 0]
                occupied = set(occupied_list)
                
                for t in targets:
                    for ny, nx in get_reading_order_neighbors(t.y, t.x):
                        if grid[ny][nx] != '#' and (ny, nx) not in occupied:
                            target_squares.add((ny, nx))
                
                if target_squares:
                    dists = bfs(unit.y, unit.x, units)
                    
                    reachable_squares = []
                    for (ty, tx) in target_squares:
                        if (ty, tx) in dists:
                            reachable_squares.append((dists[(ty, tx)], ty, tx))
                    
                    if reachable_squares:
                        reachable_squares.sort()
                        chosen_dist, chosen_y, chosen_x = reachable_squares[0]
                        
                        # Reverse BFS
                        # Treat unit as not occupied for reverse BFS (though it's start point)
                        # We need distances from chosen target to unit's neighbors.
                        # Pass units list excluding current unit?
                        # No, we can just pass current units. The unit is at unit.y, unit.x.
                        # It won't block the path *to* its neighbors.
                        # However, strictly speaking, BFS logic treats unit positions as blocked.
                        # So we should pass a list without 'unit'.
                        
                        other_units = [u for u in units if u != unit]
                        back_dists = bfs(chosen_y, chosen_x, other_units)
                        
                        best_step = None
                        min_step_dist = float('inf')
                        
                        for ny, nx in get_reading_order_neighbors(unit.y, unit.x):
                            if (ny, nx) in back_dists:
                                d = back_dists[(ny, nx)]
                                if d < min_step_dist:
                                    min_step_dist = d
                                    best_step = (ny, nx)
                        
                        if best_step:
                            unit.y, unit.x = best_step

            # --- ATTACK PHASE ---
            adjacent_enemies = []
            targets = [u for u in units if u.hp > 0 and u.type != unit.type] # Refresh targets
            for t in targets:
                if abs(unit.y - t.y) + abs(unit.x - t.x) == 1:
                    adjacent_enemies.append(t)
            
            if adjacent_enemies:
                adjacent_enemies.sort(key=lambda u: (u.hp, u.y, u.x))
                target = adjacent_enemies[0]
                
                target.hp -= unit.attack_power
                if target.hp <= 0:
                    if target.type == 'E':
                        return False, 0 # Elf died
        
        if combat_ended:
            total_hp = sum(u.hp for u in units if u.hp > 0)
            return True, rounds * total_hp
            
        rounds += 1

def solve():
    with open("input.txt") as f:
        lines = [line.rstrip() for line in f]
    
    # Binary search or Linear search?
    # Linear search from 4 is safer to find the minimal.
    # We can skip a bit if needed, but let's just start at 4.
    
    attack_power = 4
    while True:
        # print(f"Testing attack power: {attack_power}")
        success, outcome = run_simulation(attack_power, lines)
        if success:
            print(f"Success with attack power {attack_power}")
            print(f"Outcome: {outcome}")
            break
        attack_power += 1

solve()
