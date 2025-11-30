import sys
import os
from collections import deque

# Check for PIL
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL not available, skipping visualization.")

def generate_visualization():
    if not PIL_AVAILABLE:
        return

    # Simulation Logic (Copied and adapted)
    class Unit:
        def __init__(self, y, x, u_type):
            self.y = y
            self.x = x
            self.type = u_type
            self.hp = 200
            self.attack_power = 3
            self.max_hp = 200

    with open("input.txt") as f:
        lines = [line.rstrip() for line in f]

    height = len(lines)
    width = len(lines[0])
    
    grid_map = []
    units = []
    
    for r, line in enumerate(lines):
        row = []
        for c, char in enumerate(line):
            if char in 'GE':
                units.append(Unit(r, c, char))
                row.append('.') 
            else:
                row.append(char)
        grid_map.append(row)

    def get_reading_order_neighbors(y, x):
        candidates = [(y-1, x), (y, x-1), (y, x+1), (y+1, x)]
        return [(ny, nx) for ny, nx in candidates if 0 <= ny < height and 0 <= nx < width]

    def bfs(start_y, start_x, current_units):
        q = deque([(start_y, start_x, 0)])
        visited = {(start_y, start_x): 0}
        occupied = set((u.y, u.x) for u in current_units if u.hp > 0)
        while q:
            y, x, dist = q.popleft()
            for ny, nx in get_reading_order_neighbors(y, x):
                if grid_map[ny][nx] == '#' or (ny, nx) in occupied: continue
                if (ny, nx) not in visited:
                    visited[(ny, nx)] = dist + 1
                    q.append((ny, nx, dist + 1))
        return visited

    # Visualization settings
    CELL_SIZE = 20
    IMG_W, IMG_H = width * CELL_SIZE, height * CELL_SIZE
    
    # Colors
    COLOR_WALL = (50, 50, 50)
    COLOR_FLOOR = (200, 200, 200)
    COLOR_ELF = (0, 200, 0)
    COLOR_GOBLIN = (200, 0, 0)
    COLOR_HP_BAR_BG = (100, 100, 100)
    COLOR_HP_BAR_FG = (0, 255, 0)

    frames = []

    def draw_frame(round_num):
        img = Image.new('RGB', (IMG_W, IMG_H), COLOR_FLOOR)
        draw = ImageDraw.Draw(img)
        
        # Draw Map
        for r in range(height):
            for c in range(width):
                if grid_map[r][c] == '#':
                    x0, y0 = c * CELL_SIZE, r * CELL_SIZE
                    draw.rectangle([x0, y0, x0 + CELL_SIZE - 1, y0 + CELL_SIZE - 1], fill=COLOR_WALL)
        
        # Draw Units
        for u in units:
            if u.hp <= 0: continue
            cx, cy = u.x * CELL_SIZE + CELL_SIZE // 2, u.y * CELL_SIZE + CELL_SIZE // 2
            radius = CELL_SIZE // 2 - 2
            color = COLOR_ELF if u.type == 'E' else COLOR_GOBLIN
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color)
            
            # HP Bar
            hp_ratio = u.hp / u.max_hp
            bar_w = CELL_SIZE - 4
            bar_h = 3
            bx, by = u.x * CELL_SIZE + 2, u.y * CELL_SIZE + CELL_SIZE - 5
            draw.rectangle([bx, by, bx + bar_w, by + bar_h], fill=COLOR_HP_BAR_BG)
            draw.rectangle([bx, by, bx + int(bar_w * hp_ratio), by + bar_h], fill=COLOR_HP_BAR_FG)

        # Draw Round Text
        # draw.text((10, 10), f"Round: {round_num}", fill=(0, 0, 0)) # Requires font
        
        return img

    rounds = 0
    # Save initial state
    frames.append(draw_frame(0))

    while True:
        units.sort(key=lambda u: (u.y, u.x))
        combat_ended = False
        
        for i, unit in enumerate(units):
            if unit.hp <= 0: continue
            targets = [u for u in units if u.hp > 0 and u.type != unit.type]
            if not targets:
                combat_ended = True
                break
                
            # Move
            in_range = False
            for t in targets:
                if abs(unit.y - t.y) + abs(unit.x - t.x) == 1:
                    in_range = True; break
            
            if not in_range:
                target_squares = set()
                occupied = set((u.y, u.x) for u in units if u.hp > 0)
                for t in targets:
                    for ny, nx in get_reading_order_neighbors(t.y, t.x):
                        if grid_map[ny][nx] != '#' and (ny, nx) not in occupied:
                            target_squares.add((ny, nx))
                
                if target_squares:
                    dists = bfs(unit.y, unit.x, units)
                    reachable = []
                    for (ty, tx) in target_squares:
                        if (ty, tx) in dists:
                            reachable.append((dists[(ty, tx)], ty, tx))
                    if reachable:
                        reachable.sort()
                        chosen_dist, chosen_y, chosen_x = reachable[0]
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

            # Attack
            adjacent = []
            targets = [u for u in units if u.hp > 0 and u.type != unit.type]
            for t in targets:
                if abs(unit.y - t.y) + abs(unit.x - t.x) == 1:
                    adjacent.append(t)
            if adjacent:
                adjacent.sort(key=lambda u: (u.hp, u.y, u.x))
                target = adjacent[0]
                target.hp -= unit.attack_power
        
        rounds += 1
        # Capture frame at end of round
        frames.append(draw_frame(rounds))
        
        if combat_ended:
            break
            
        units = [u for u in units if u.hp > 0] # clean dead
        
    # Save frames as GIF
    if frames:
        frames[0].save('battle.gif', save_all=True, append_images=frames[1:], optimize=True, duration=100, loop=0)
        print(f"GIF saved with {len(frames)} frames.")

generate_visualization()
