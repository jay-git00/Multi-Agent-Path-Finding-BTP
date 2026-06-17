import sys
import os

def generate_kinematic_map(output_file, num_rows_blocks=4, num_cols_blocks=3, 
                           rack_width=15, rack_height=2, 
                           road_width=5, home_width=5):
    """
    Generates a warehouse map with wide roads suitable for large kinematic robots.
    
    Structure:
    - Racks are rectangular blocks of size (rack_width x rack_height) filled with '@'
    - Endpoints 'e' are placed above and below the racks
    - Roads '.' are 'road_width' cells wide between all rack blocks
    - Home zones 'r' are placed on the left and right sides
    """
    
    # Calculate total dimensions
    # Each block is: road + endpoint + gap + rack + gap + endpoint
    # Plus a final road at the bottom/right
    
    # A single rack group height = rack_height + 2 (endpoints) + 2 (gaps)
    rack_group_height = rack_height + 4
    
    # Total height = (road_width + rack_group_height) * num_rows_blocks + road_width
    total_height = (road_width + rack_group_height) * num_rows_blocks + road_width
    
    # Total width = home_width (left) + road_width + 
    #               (rack_width + road_width) * num_cols_blocks + 
    #               home_width (right)
    total_width = home_width + road_width + (rack_width + road_width) * num_cols_blocks + home_width
    
    # Initialize map with all roads
    grid = [['.' for _ in range(total_width)] for _ in range(total_height)]
    
    # Fill left and right home zones
    for r in range(total_height):
        for c in range(home_width):
            grid[r][c] = 'r'
            grid[r][total_width - 1 - c] = 'r'
            
    # Fill racks and endpoints
    num_endpoints = 0
    num_racks = 0
    
    for row_idx in range(num_rows_blocks):
        for col_idx in range(num_cols_blocks):
            # Calculate top-left corner of this rack group
            start_r = road_width + row_idx * (rack_group_height + road_width)
            start_c = home_width + road_width + col_idx * (rack_width + road_width)
            
            # Top endpoints
            for c in range(start_c, start_c + rack_width):
                grid[start_r][c] = 'e'
                num_endpoints += 1
                
            # Rack body (offset by 2 because of top endpoint + 1 gap)
            for r in range(start_r + 2, start_r + 2 + rack_height):
                for c in range(start_c, start_c + rack_width):
                    grid[r][c] = '@'
                    num_racks += 1
                    
            # Bottom endpoints (offset by rack_height + 3)
            for c in range(start_c, start_c + rack_width):
                grid[start_r + 3 + rack_height][c] = 'e'
                num_endpoints += 1

    # Write to file
    with open(output_file, 'w') as f:
        f.write(f'{total_height},{total_width}\n')
        # Placeholder counts for endpoints, workstations, etc. (RHCR needs these)
        f.write(f'{num_endpoints}\n')
        f.write('0\n') # Workstations
        f.write('5000\n') # Some arbitrary number from original
        
        for r in range(total_height):
            f.write(''.join(grid[r]) + '\n')
            
    print(f"Generated kinematic map: {total_height}x{total_width}")
    print(f"Road width: {road_width} cells (Allows 5x1 robots to turn smoothly)")

if __name__ == '__main__':
    # We want a road width of 5 so a 5x1 robot can rotate 
    # within the intersection without hitting anything.
    generate_kinematic_map('c:/Users/DILEEP/MATLAB/Projects/untitled/BTP/MAPF-with-multi-level-architecture/RHCR-master/maps/kiva_kinematic.map',
                           num_rows_blocks=5, num_cols_blocks=4,
                           rack_width=15, rack_height=2, road_width=5, home_width=5)
