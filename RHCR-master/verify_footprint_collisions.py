import argparse
import sys
from collections import defaultdict

def load_map(map_path):
    with open(map_path, 'r') as f:
        lines = f.readlines()
    
    # Line 1: rows,cols
    rows_str, cols_str = lines[0].strip().split(',')
    cols = int(cols_str)
    
    grid = []
    # Map starts at line 5 (index 4)
    for line in lines[4:]:
        if line.strip():
            grid.append(list(line.strip()))
    return cols, grid

def load_paths(paths_path):
    paths = {}
    with open(paths_path, 'r') as f:
        lines = f.readlines()
    
    if not lines:
        return paths
        
    num_agents = int(lines[0].strip())
    for a in range(num_agents):
        path_str = lines[a + 1].strip()
        locations = []
        if path_str:
            for step in path_str.split(';'):
                if not step: continue
                loc = int(step.split(',')[0])
                locations.append(loc)
        paths[a] = locations
    return paths

def get_footprint_cells(center_loc, cols, footprint_size):
    """Returns a set of (x, y) coordinates occupied by the NxN footprint."""
    cx = center_loc % cols
    cy = center_loc // cols
    
    offset = footprint_size // 2
    cells = set()
    for dy in range(-offset, offset + 1):
        for dx in range(-offset, offset + 1):
            cells.add((cx + dx, cy + dy))
    return cells

def verify_paths(paths, cols, footprint_size):
    max_t = max(len(p) for p in paths.values())
    agents = list(paths.keys())
    
    vertex_conflicts = 0
    edge_conflicts = 0
    
    # 1. Check Vertex Conflicts (Footprint overlap at the identical timestep)
    print("Checking for vertex conflicts...")
    for t in range(max_t):
        occupied_at_t = {}
        for a in agents:
            # If agent finished its path, it stays at its last location
            loc = paths[a][t] if t < len(paths[a]) else paths[a][-1]
            cells = get_footprint_cells(loc, cols, footprint_size)
            occupied_at_t[a] = cells
            
        for i in range(len(agents)):
            for j in range(i + 1, len(agents)):
                a1 = agents[i]
                a2 = agents[j]
                overlap = occupied_at_t[a1].intersection(occupied_at_t[a2])
                if overlap:
                    print(f"❌ VERTEX CONFLICT: Agents {a1} and {a2} overlap at timestep {t}.")
                    print(f"   overlapping cells: {overlap}")
                    vertex_conflicts += 1

    # 2. Check Edge/Swap Conflicts
    # A swap conflict occurs if Agent 1 moves into cells Agent 2 is vacating, AND
    # Agent 2 simultaneously moves into cells Agent 1 is vacating.
    print("Checking for edge/swap conflicts...")
    for t in range(max_t - 1):
        for i in range(len(agents)):
            for j in range(i + 1, len(agents)):
                a1 = agents[i]
                a2 = agents[j]
                
                loc1_cur = paths[a1][t] if t < len(paths[a1]) else paths[a1][-1]
                loc2_cur = paths[a2][t] if t < len(paths[a2]) else paths[a2][-1]
                loc1_next = paths[a1][t + 1] if t + 1 < len(paths[a1]) else paths[a1][-1]
                loc2_next = paths[a2][t + 1] if t + 1 < len(paths[a2]) else paths[a2][-1]
                
                # If neither moved, no new edge conflict
                if loc1_cur == loc1_next and loc2_cur == loc2_next:
                    continue
                    
                fp1_cur = get_footprint_cells(loc1_cur, cols, footprint_size)
                fp2_cur = get_footprint_cells(loc2_cur, cols, footprint_size)
                fp1_next = get_footprint_cells(loc1_next, cols, footprint_size)
                fp2_next = get_footprint_cells(loc2_next, cols, footprint_size)
                
                # A swap clip is defined as: A1's next state intersects A2's current state
                # AND A2's next state intersects A1's current state
                a1_clips_a2 = fp1_next.intersection(fp2_cur)
                a2_clips_a1 = fp2_next.intersection(fp1_cur)
                
                if a1_clips_a2 and a2_clips_a1:
                    print(f"❌ EDGE/SWAP CONFLICT: Agents {a1} and {a2} clip each other swapping at t={t}->{t+1}.")
                    print(f"   A1 next intersects A2 cur: {a1_clips_a2}")
                    print(f"   A2 next intersects A1 cur: {a2_clips_a1}")
                    edge_conflicts += 1

    print("\n==================================")
    print("VERIFICATION RESULTS")
    print("==================================")
    print(f"Vertex Conflicts: {vertex_conflicts}")
    print(f"Edge Conflicts:   {edge_conflicts}")
    
    if vertex_conflicts == 0 and edge_conflicts == 0:
        print("\n✅ SUCCESS: Paths are 100% collision-free for {}x{} footprint!".format(footprint_size, footprint_size))
        return True
    else:
        print("\n❌ FAILED: Collisions detected.")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", required=True)
    parser.add_argument("--paths", required=True)
    parser.add_argument("--footprint", type=int, default=3)
    args = parser.parse_args()
    
    cols, _ = load_map(args.map)
    paths = load_paths(args.paths)
    
    print(f"Loaded map with width {cols}")
    print(f"Loaded {len(paths)} agent paths")
    
    success = verify_paths(paths, cols, args.footprint)
    sys.exit(0 if success else 1)
