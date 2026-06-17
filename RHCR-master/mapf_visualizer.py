import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle, Circle
from matplotlib.transforms import Affine2D
from matplotlib.collections import LineCollection
import matplotlib.colors as mcolors
import os
import math

class GeneralizedKivaVisualizer:
    def __init__(self, map_file='kiva.map', results_file='my_results_paths.txt', tasks_file=None):
        print("Loading Generalized Kiva Warehouse MAPF data...")
        
        # Load data
        self.map_data = self.load_kiva_map(map_file)
        self.grid_height,self.grid_width = self.map_data.shape
        self.raw_data = self.load_raw_data(results_file)
        self.tasks_data = self.load_tasks_data(tasks_file)
        self.results_dir = os.path.dirname(results_file) if results_file else ""
        self.solution = self.convert_to_solution()
        
        # **ADAPTIVE SETUP: Configure based on robot count**
        self.num_agents = len(self.solution['agents'])
        self.setup_adaptive_parameters()
        
        # Pre-cache warehouse statistics
        self.warehouse_stats = {
            'shelves': np.sum(self.map_data == '@'),
            'endpoints': np.sum(self.map_data == 'e'),
            'robot_zones': np.sum(self.map_data == 'r'),
            'free_space': np.sum(self.map_data == '.')
        }
        
        # Identify shelf corridors for visual semantics
        self.shelf_corridors = set()
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.map_data[y, x] == 'e':
                    # Check neighbors for shelves
                    for dy, dx in [(0,1), (0,-1), (1,0), (-1,0)]:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < self.grid_height and 0 <= nx < self.grid_width:
                            if self.map_data[ny, nx] == '@':
                                self.shelf_corridors.add(y * self.grid_width + x)
                                break
        
        print(f"DEBUG: Found {len(self.shelf_corridors)} shelf-adjacent corridors.")
        print(f"DEBUG: Found {self.warehouse_stats['shelves']} shelves.")
        
        # Setup visualization
        self.setup_adaptive_layout()
        self.current_timestep = 0
        self.frames_per_step = 1   # Strict 1-to-1 timesteps, no intermediate frames
        self.fp_width = 3   # default, overridden from CLI
        self.fp_height = 1
        self.max_timestep = max(len(path) for path in self.solution['agents'].values()) if self.solution['agents'] else 1
        
        # Pre-render static elements (Shelves, Endpoints)
        self.setup_static_warehouse()
        self.agent_artists = []
        self.trail_artists = []
        self.track_artists = []
        
        # Pre-render robot tracks (High Alpha = Clumsy, Low Alpha = Professional)
        self.render_static_tracks()
        
        print(f"SUCCESS: Generalized visualizer ready for {self.num_agents} robots")
        print(f"Mode: {self.viz_mode} | Grid: {self.grid_width}x{self.grid_height}")

    def setup_adaptive_parameters(self):
        """Configure visualization parameters based on robot count"""
        
        if self.num_agents <= 10:
            self.viz_mode = "DETAILED"
            self.robot_size = 0.8
            self.font_size = 12 # Increased from 10
            self.trail_length = 12
            self.trail_alpha = 0.7
            self.show_individual_status = True
            self.show_robot_ids = True
            self.grid_detail = "high"
            
        elif self.num_agents <= 30:
            self.viz_mode = "MEDIUM"
            self.robot_size = 0.5
            self.font_size = 8
            self.trail_length = 8
            self.trail_alpha = 0.5
            self.show_individual_status = True
            self.show_robot_ids = True
            self.grid_detail = "medium"
            
        elif self.num_agents <= 100:
            self.viz_mode = "COMPACT"
            self.robot_size = 0.3
            self.font_size = 7
            self.trail_length = 20 # Increased for better track visibility
            self.trail_alpha = 0.3
            self.show_individual_status = False
            self.show_robot_ids = True
            self.grid_detail = "low"
            
        elif self.num_agents <= 500:
            self.viz_mode = "DENSE"
            self.robot_size = 0.15
            self.font_size = 4
            self.trail_length = 3
            self.trail_alpha = 0.3
            self.show_individual_status = False
            self.show_robot_ids = False
            self.grid_detail = "minimal"
            
        else:  # 500+ robots
            self.viz_mode = "HEATMAP"
            self.robot_size = 0.1
            self.font_size = 0
            self.trail_length = 2
            self.trail_alpha = 0.2
            self.show_individual_status = False
            self.show_robot_ids = False
            self.grid_detail = "none"
        
        # **ADAPTIVE COLOR SCHEME**
        self.setup_adaptive_colors()
        
        # **ADAPTIVE ANIMATION SPEED**
        if self.num_agents <= 10:
            self.animation_interval = 200   # 5 discrete steps per second
        elif self.num_agents <= 50:
            self.animation_interval = 250
        elif self.num_agents <= 200:
            self.animation_interval = 300
        else:
            self.animation_interval = 400

    def setup_adaptive_colors(self):
        """Generate colors and state colors"""
        if self.num_agents <= 12:
            self.colors = plt.cm.Set3(np.linspace(0, 1, max(self.num_agents, 1)))
        elif self.num_agents <= 50:
            colors = []
            maps = ['Set3', 'Dark2', 'Paired', 'Accent']
            per_map = math.ceil(self.num_agents / len(maps))
            for i, cmap_name in enumerate(maps):
                start_idx = i * per_map
                end_idx = min((i + 1) * per_map, self.num_agents)
                if start_idx < self.num_agents:
                    cmap = plt.cm.get_cmap(cmap_name)
                    colors.extend([cmap(j / per_map) for j in range(end_idx - start_idx)])
            self.colors = np.array(colors[:self.num_agents])
        else:
            self.colors = plt.cm.rainbow(np.linspace(0, 1, self.num_agents))
        
        # State-based colors
        self.color_idle = 'gray'
        self.color_picking = 'lime'
        self.color_collision_risk = 'red'
        self.color_background = '#1a1a1a' # Dark theme support

    def setup_adaptive_layout(self):
        """Setup figure layout based on visualization mode"""
        if self.viz_mode in ["DETAILED", "MEDIUM", "COMPACT"]:
            # Two-panel layout with info
            self.fig, (self.ax_main, self.ax_info) = plt.subplots(1, 2, figsize=(22, 12), gridspec_kw={'width_ratios': [3, 1]})
            self.use_info_panel = True
        elif self.viz_mode in ["DENSE"]:
            # Main plot with minimal info overlay
            self.fig, self.ax_main = plt.subplots(1, 1, figsize=(16, 12))
            self.use_info_panel = False
        else:  # HEATMAP mode
            # Full screen visualization
            self.fig, self.ax_main = plt.subplots(1, 1, figsize=(18, 14))
            self.use_info_panel = False

    def setup_static_warehouse(self):
        """Pre-render static warehouse elements"""
        self.ax_main.set_xlim(-0.5, self.grid_width - 0.5)
        self.ax_main.set_ylim(-0.5, self.grid_height - 0.5)
        self.ax_main.set_aspect('equal')
        
        # **ADAPTIVE WAREHOUSE RENDERING**
        if self.grid_detail == "high":
            # Full detail for small robot counts
            self.render_detailed_warehouse()
        elif self.grid_detail == "medium":
            # Simplified rendering
            self.render_medium_warehouse()
        elif self.grid_detail == "low":
            # Basic shapes only
            self.render_basic_warehouse()
        elif self.grid_detail == "minimal":
            # Just obstacles
            self.render_minimal_warehouse()
        else:  # "none"
            # Background color coding only
            self.render_background_only()
        
        # **ADAPTIVE GRID LINES**
        if self.grid_detail in ["high", "medium"]:
            spacing = 5 if self.grid_detail == "high" else 10
            for x in range(0, self.grid_width, spacing):
                self.ax_main.axvline(x - 0.5, color='lightgray', linewidth=0.2, alpha=0.5)
            for y in range(0, self.grid_height, spacing):
                self.ax_main.axhline(y - 0.5, color='lightgray', linewidth=0.2, alpha=0.5)

    def render_detailed_warehouse(self):
        """Full warehouse detail with clear roads"""
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                cell = self.map_data[y, x]
                
                if cell == '@':
                    # High contrast SHELF: Dark Brown with thick border
                    rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor='#4E342E', edgecolor='black', linewidth=2, alpha=1.0)
                    self.ax_main.add_patch(rect)
                elif cell == 'e':
                    # High contrast CORRIDOR: Vivid Orange
                    if (y * self.grid_width + x) in self.shelf_corridors:
                         rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor='#FF6D00', edgecolor='#E65100', linewidth=1, alpha=0.9)
                    else:
                         rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor='#FF9800', alpha=0.6)
                    self.ax_main.add_patch(rect)
                elif cell == 'r':
                    rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor='lightblue', edgecolor='blue', alpha=0.6)
                    self.ax_main.add_patch(rect)
                    self.ax_main.text(x, y, 'R', ha='center', va='center', fontweight='bold', fontsize=6, color='darkblue')
                elif cell == '.':
                    # Safety Floor: Light Gray with white markings
                    rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor='#f5f5f5', edgecolor='white', linewidth=0.5, zorder=-2)
                    self.ax_main.add_patch(rect)

    def render_medium_warehouse(self):
        """Simplified warehouse with highlighted roads"""
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                cell = self.map_data[y, x]
                
                if cell == '@':
                    rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor='brown', alpha=0.8)
                    self.ax_main.add_patch(rect)
                elif cell == 'e':
                    rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor='orange', alpha=0.7)
                    self.ax_main.add_patch(rect)
                elif cell == 'r':
                    rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor='lightblue', alpha=0.5)
                    self.ax_main.add_patch(rect)
                elif cell == '.':
                    # Standard warehouse floor
                    rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor='#fafafa', edgecolor='#f0f0f0', linewidth=0.4, zorder=-2)
                    self.ax_main.add_patch(rect)

    def render_basic_warehouse(self):
        """Basic warehouse with high-contrast grid roads for clarity"""
        shelf_coords = np.where(self.map_data == '@')
        endpoint_coords = np.where(self.map_data == 'e')
        road_coords = np.where(self.map_data == '.')
        home_coords = np.where(self.map_data == 'r')
        
        # Roads: Light gray tiles with distinct steel borders
        for y, x in zip(road_coords[0], road_coords[1]):
            rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor='#f0f2f5', edgecolor='#c1c9d2', linewidth=0.2, zorder=-2)
            self.ax_main.add_patch(rect)
            
        # Home/Starting Boxes: Vibrant Visible Blue
        for y, x in zip(home_coords[0], home_coords[1]):
            rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor='#bbdefb', edgecolor='#1976d2', linewidth=0.8, zorder=-2)
            self.ax_main.add_patch(rect)
            
        # Shelves: Heavy dark blocks
        for y, x in zip(shelf_coords[0], shelf_coords[1]):
            rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor='#4a4a4a', edgecolor='black', linewidth=0.8)
            self.ax_main.add_patch(rect)
            
        # Endpoints: Vibrant orange targets
        for y, x in zip(endpoint_coords[0], endpoint_coords[1]):
            rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor='#ff6b00', edgecolor='darkred', linewidth=0.8)
            self.ax_main.add_patch(rect)

    def render_minimal_warehouse(self):
        """Minimal warehouse for 100-500 robots"""
        # Only show obstacles as scatter plot for performance
        shelf_coords = np.where(self.map_data == '@')
        if len(shelf_coords[0]) > 0:
            self.ax_main.scatter(shelf_coords[1], shelf_coords[0], c='brown', s=4, alpha=0.5, marker='s')
        
        endpoint_coords = np.where(self.map_data == 'e')
        if len(endpoint_coords[0]) > 0:
            self.ax_main.scatter(endpoint_coords[1], endpoint_coords[0], c='orange', s=4, alpha=0.5, marker='s')

    def render_background_only(self):
        """Render the underlying map grid with warehouse aesthetics"""
        self.ax_main.clear()
        
        # Colors for warehouse semantics
        color_shelf = '#8B4513'     # SaddleBrown
        color_accessible_rack = '#FF8C00'  # DarkOrange (Accessible Racks/Tasks)
        color_free = '#F0F0F0'      # LightGrey (Corridors/Travel)
        color_home = '#4682B4'      # SteelBlue (Robot rests)

        for y in range(self.map_data.shape[0]):
            for x in range(self.map_data.shape[1]):
                cell = self.map_data[y, x]
                rect_x, rect_y = self.location_to_xy(y * self.map_data.shape[1] + x)
                
                # Default style
                cell_color = color_free
                alpha = 0.5
                zorder = 0
                
                if cell == '@': # Shelf
                    cell_color = color_shelf
                    alpha = 0.9
                    zorder = 1
                elif cell == 'e': # Accessible Rack (Tasks)
                    cell_color = color_accessible_rack
                    alpha = 0.7
                    zorder = 1
                elif cell == 'r': # Home
                    cell_color = color_home
                    alpha = 0.6
                
                rect = Rectangle((rect_x - 0.5, rect_y - 0.5), 1, 1, 
                                 facecolor=cell_color, alpha=alpha, 
                                 edgecolor='#CCCCCC', linewidth=0.2, zorder=zorder)
                self.ax_main.add_patch(rect)
                
                # Add "Shelf" visual hint
                if cell == '@':
                    self.ax_main.add_patch(Rectangle((rect_x - 0.4, rect_y - 0.4), 0.8, 0.8, 
                                          fill=False, edgecolor='#603010', linewidth=0.5, zorder=2))

        self.ax_main.set_xlim(-1, self.map_data.shape[1])
        self.ax_main.set_ylim(-1, self.map_data.shape[0])
        self.ax_main.set_aspect('equal')
        self.ax_main.axis('off')
        
        # Add Legend for Map Semantics
        from matplotlib.lines import Line2D
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=color_shelf, edgecolor='#603010', label='Solid Racks (@) - Inaccessible Storage'),
            Patch(facecolor=color_accessible_rack, edgecolor='#CC7000', label='Accessible Racks (e) - Task Locations'),
            Patch(facecolor=color_home, edgecolor='#306090', label='Robot Zones (r) - Home'),
            Patch(facecolor=color_free, edgecolor='#CCCCCC', label='Corridors/Travel Area (.)'),
            Line2D([0], [0], marker='s', color='w', markerfacecolor=self.color_picking, 
                   markersize=10, label='Robot Interaction (Loading/Unloading)')
        ]
        self.ax_main.legend(handles=legend_elements, loc='upper right', 
                           bbox_to_anchor=(1.15, 1.0), fontsize=8, frameon=True, shadow=True)

    def render_static_tracks(self):
        """Draw faint 'rails' for the entire robot history"""
        if self.viz_mode == "HEATMAP":
            return
        for agent_id, path in self.solution['agents'].items():
            if len(path) > 1:
                color = self.colors[agent_id % len(self.colors)]
                tx = [p[0] for p in path]
                ty = [p[1] for p in path]
                # Slightly more visible (0.1) for clarity, but still faint
                line, = self.ax_main.plot(tx, ty, color=color, alpha=0.1, linewidth=0.5, zorder=0)
                self.track_artists.append(line)

    def update_dynamic_elements(self, timestep):
        """Adaptive robot rendering based on count"""
        # Clear previous elements
        for artist in self.agent_artists + self.trail_artists:
            artist.remove()
        self.agent_artists.clear()
        self.trail_artists.clear()
        
        if self.viz_mode == "HEATMAP":
            return self.render_heatmap_mode(timestep)
        else:
            return self.render_individual_robots(timestep)

    def render_individual_robots(self, float_timestep):
        """Render robots as realistic rigid bodies (Addverb style)."""
        timestep = int(float_timestep)
        progress = float_timestep - timestep
        robot_status = []
        active_count = 0
        picking_count = 0
        completed_count = 0
        total_tasks_completed = 0

        # Base footprint dimensions
        fp_w_base = self.fp_width
        fp_h_base = self.fp_height

        for agent_id, path in self.solution['agents'].items():
            # Task bookkeeping
            robot_tasks = self.tasks_data.get(agent_id, [])
            tasks_done = sum(1 for _, t in robot_tasks if 0 <= t <= timestep)
            total_tasks_completed += tasks_done

            next_goal_xy = None
            is_currently_picking = False
            for loc_id, t in robot_tasks:
                if t > timestep:
                    next_goal_xy = self.location_to_xy(loc_id)
                    break
                if t == timestep:
                    is_currently_picking = True

            if timestep < len(path):
                x, y, theta = path[timestep]
                if timestep + 1 < len(path):
                    nx, ny, ntheta = path[timestep + 1]
                    x = x + (nx - x) * progress
                    y = y + (ny - y) * progress
                    
                    diff = (ntheta - theta) % 4
                    if diff == 3: diff = -1
                    theta = theta + diff * progress

                base_color = self.colors[agent_id % len(self.colors)]
                robot_color = tuple(base_color[:3]) if len(base_color) >= 3 else base_color

                # Dotted line to next goal
                if next_goal_xy and self.viz_mode in ["DETAILED", "MEDIUM"]:
                    gx, gy = next_goal_xy
                    line = self.ax_main.plot(
                        [x, gx], [y, gy], color=base_color,
                        linestyle=':', linewidth=0.4, alpha=0.2)[0]
                    self.trail_artists.append(line)

                # Rigid Body dimensions
                body_w = fp_w_base * 0.92
                body_h = fp_h_base * 0.92
                mast_w = min(body_w, body_h) * 0.40
                mast_h = max(body_w, body_h) * 0.30

                body_alpha = 0.95 if is_currently_picking else 0.85
                body_color = '#8A9A9D'
                stripe_color = robot_color
                
                shape = getattr(self, 'agent_shape', 'rect')
                # For sideloader, we CANNOT use simple Affine2D rotation because the distance
                # between the fork (center) and the body changes dynamically!
                if shape == 'sideloader':
                    # Body is ALWAYS 3 wide, 1 high
                    body_w = self.robot_size * 3
                    body_h = self.robot_size * 1
                    
                    mast_w = body_w * 0.05
                    mast_h = body_h * 0.1
                    
                    if theta == 0 or theta == 2:
                        rect_x = x - body_w / 2
                        rect_y = y - body_h / 2
                        mast_x = x - mast_w / 2
                        mast_y = y - mast_h / 2
                    elif theta == 1:
                        # South: body is North of the fork (y - 1).
                        rect_x = x - body_w / 2
                        rect_y = (y - 1) - body_h / 2
                        # Draw mast extending from body to fork
                        mast_h = 1.0 # span the gap
                        mast_x = x - mast_w / 2
                        mast_y = (y - 1)
                    elif theta == 3:
                        # North: body is South of the fork (y + 1).
                        rect_x = x - body_w / 2
                        rect_y = (y + 1) - body_h / 2
                        # Draw mast extending from body to fork
                        mast_h = 1.0
                        mast_x = x - mast_w / 2
                        mast_y = y
                    
                    stripe_w = body_w * 0.15
                    stripe_h = body_h * 0.3
                    # The stripe represents the fork, which is ALWAYS at (x,y)
                    stripe_x = x - stripe_w / 2
                    stripe_y = y - stripe_h / 2
                    
                    body_rect = Rectangle(
                        (rect_x, rect_y), body_w, body_h,
                        facecolor=body_color, alpha=body_alpha, zorder=4,
                        edgecolor='black', linewidth=1.5
                    )
                    
                    stripe = Rectangle(
                        (stripe_x, stripe_y), stripe_w, stripe_h,
                        facecolor=stripe_color, zorder=5
                    )
                    
                    mast = Rectangle(
                        (mast_x, mast_y), mast_w, mast_h,
                        facecolor='#222222', zorder=3
                    )
                    
                    self.ax_main.add_patch(body_rect)
                    self.ax_main.add_patch(stripe)
                    self.ax_main.add_patch(mast)
                    self.agent_artists.append(body_rect)
                    self.agent_artists.append(stripe)
                    self.agent_artists.append(mast)
                    continue # Skip the Affine2D rotation below

                if shape == 'forklift':
                    # (x,y) is the front (East). Body trails West.
                    rect_x = x - body_w
                    rect_y = y - body_h / 2
                    
                    stripe_w = body_w * 0.15
                    stripe_h = body_h
                    stripe_x = x - stripe_w
                    stripe_y = y - stripe_h / 2
                    
                    mast_x = x - mast_w
                    mast_y = y - mast_h / 2
                else:
                    rect_x = x - body_w / 2
                    rect_y = y - body_h / 2
                    
                    stripe_w = body_w * 0.15
                    stripe_h = body_h
                    stripe_x = x - body_w / 2
                    stripe_y = y - stripe_h / 2
                    
                    mast_x = x - mast_w / 2
                    mast_y = y - mast_h / 2

                body_rect = Rectangle(
                    (rect_x, rect_y), body_w, body_h,
                    facecolor=body_color, alpha=body_alpha, zorder=4,
                    edgecolor='black', linewidth=1.5
                )
                
                stripe = Rectangle(
                    (stripe_x, stripe_y), stripe_w, stripe_h,
                    facecolor=stripe_color, zorder=5
                )
                
                mast = Rectangle(
                    (mast_x, mast_y), mast_w, mast_h,
                    facecolor='#222222', zorder=5
                )
                
                self.ax_main.add_patch(body_rect)
                self.ax_main.add_patch(stripe)
                self.ax_main.add_patch(mast)
                self.agent_artists.append(body_rect)
                self.agent_artists.append(stripe)
                self.agent_artists.append(mast)

                # Smooth rotation
                angle_deg = 90.0 * theta
                t_rot = Affine2D().rotate_deg_around(x, y, angle_deg) + self.ax_main.transData
                body_rect.set_transform(t_rot)
                stripe.set_transform(t_rot)
                mast.set_transform(t_rot)

                # Picking glow / Task Completion Signal
                is_just_completed = False
                for loc_id, t in robot_tasks:
                    # If task was completed in the last 2 timesteps
                    if t <= timestep <= t + 2:
                        tx, ty = self.location_to_xy(loc_id)
                        # Check if robot is physically near the endpoint
                        if abs(x - tx) + abs(y - ty) < 2.0:
                            is_just_completed = True
                            break

                if is_just_completed or is_currently_picking:
                    # BIG glow signal to make task completion extremely clear
                    glow = Circle((x, y), max(fp_w_base, fp_h_base)*0.8, facecolor='#FFD700',
                                  edgecolor='red', linewidth=2, alpha=0.6, zorder=8)
                    self.ax_main.add_patch(glow)
                    self.agent_artists.append(glow)
                    
                    # Add a text label "PICK!"
                    pick_text = self.ax_main.text(x, y + 0.5, "TASK!", ha='center', va='bottom',
                                                fontweight='bold', fontsize=self.font_size+2,
                                                color='yellow', bbox=dict(facecolor='red', alpha=0.7, boxstyle='round,pad=0.1'), zorder=9)
                    self.agent_artists.append(pick_text)

                # Task waypoint markers
                for loc_id, t in robot_tasks:
                    if t <= timestep:
                        tx, ty = self.location_to_xy(loc_id)
                        marker = Circle((tx, ty), self.robot_size * 0.3,
                                        facecolor=base_color, alpha=0.3, zorder=1)
                        self.ax_main.add_patch(marker)
                        self.agent_artists.append(marker)

                # Robot ID label
                if self.show_robot_ids and self.font_size > 0:
                    task_type = "..."
                    goal_loc_id = None
                    if agent_id in self.tasks_data:
                        for loc_id, t in self.tasks_data[agent_id]:
                            if t >= timestep:
                                goal_loc_id = loc_id
                                break
                    if goal_loc_id is not None:
                        task_type = "In" if goal_loc_id in self.shelf_corridors else "Out"

                    label = f"R{agent_id}:{task_type}"
                    if tasks_done > 0:
                        label += f" ({tasks_done})"
                    text = self.ax_main.text(
                        x, y - 1.0, label, ha='center', va='top',
                        fontweight='bold', fontsize=self.font_size - 1,
                        color='white',
                        bbox=dict(boxstyle="round,pad=0.2",
                                  facecolor='black', alpha=0.5))
                    self.agent_artists.append(text)

                # Status tracking
                iy, ix = int(y), int(x)
                cell_type = self.map_data[iy, ix] if 0 <= iy < self.grid_height and 0 <= ix < self.grid_width else '?'
                if cell_type == 'e':
                    picking_count += 1
                    robot_status.append(f"R{agent_id}: At Endpoint ({tasks_done} total)")
                else:
                    active_count += 1
                    robot_status.append(f"R{agent_id}: Active (Tasks: {tasks_done})")
            else:
                completed_count += 1
                robot_status.append(f"R{agent_id}: FINISHED ({tasks_done} tasks)")

        metrics = self.load_solver_metrics(timestep)
        eff = total_tasks_completed / (timestep + 1)
        summary = f"Robots: {self.num_agents} | Tasks: {total_tasks_completed} | Throughput: {eff:.2f}/t"
        self.ax_main.set_title(summary, fontsize=16, fontweight='bold', color='darkblue', pad=30)

        return robot_status, {'active': active_count, 'picking': picking_count,
                              'completed': completed_count,
                              'total_tasks': total_tasks_completed,
                              'metrics': metrics}

    def render_heatmap_mode(self, timestep):
        """Heatmap visualization for 500+ robots"""
        # Create density heatmap
        density_map = np.zeros((self.grid_height, self.grid_width))
        
        for agent_id, path in self.solution['agents'].items():
            if timestep < len(path):
                x, y = path[timestep]
                if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                    density_map[y, x] += 1
        
        # Clear previous heatmap
        for artist in self.agent_artists:
            artist.remove()
        self.agent_artists.clear()
        
        # Draw heatmap
        if np.max(density_map) > 0:
            im = self.ax_main.imshow(density_map, cmap='hot', alpha=0.7, 
                                   extent=[-0.5, self.grid_width-0.5, self.grid_height-0.5, -0.5])
            self.agent_artists.append(im)
        
        active_robots = np.sum(density_map)
        self.ax_main.set_title(f'Kiva Warehouse Heatmap - {int(active_robots)} Active Robots - Step: {timestep}', 
                              fontsize=12, fontweight='bold')
        
        return [], {'active': int(active_robots), 'picking': 0, 'completed': self.num_agents - int(active_robots)}

    def update_info_panel(self, timestep, robot_status, summary_stats):
        """Adaptive info panel"""
        if not self.use_info_panel:
            return
            
        self.ax_info.clear()
        self.ax_info.set_xlim(0, 10)
        self.ax_info.set_ylim(0, 10)
        self.ax_info.axis('off')
        
        if self.viz_mode in ["DETAILED", "MEDIUM", "COMPACT"]:
            metrics = summary_stats.get('metrics', {})
            # Scientific Dashboard on the Sidebar
            info_text = f"""--- SYSTEM DASHBOARD ---
MODE: {self.viz_mode}
AGENTS: {self.num_agents}
STRATEGY: APS + CFNRS
SAFETY: [ ACTIVE ]
----------------------------
SCIENTIFIC METRICS:
• Nodes Exp: {int(metrics.get('nodes', 0)):,}
• Wait Spots: {int(metrics.get('collisions', 0))}
• Tick Time: {metrics.get('runtime', 0.0):.3f}s
• Throughput: {summary_stats['total_tasks']/(timestep+1):.2f}/t
• Path Gap: {int(metrics.get('cost', 0) - metrics.get('min_cost', 0))}
----------------------------
WAREHOUSE STATUS:
• Active: {summary_stats['active']}
• Picking: {summary_stats['picking']}
• Finished: {summary_stats['completed']}
• Jobs Done: {int(summary_stats.get('total_tasks', 0))}

PROGRESS:
• Timestep: {timestep}/{self.max_timestep-1}
• Timeline: {timestep/self.max_timestep*100:.1f}%
----------------------------
INDIVIDUAL STATUS:
{chr(10).join(robot_status[:10])}
{f"... and {len(robot_status)-10} more" if len(robot_status)>10 else ""}"""


        else:  # MEDIUM mode
            # Summary mode
            info_text = f"""KIVA WAREHOUSE - SUMMARY VIEW
=============================
{self.num_agents} Robots (Mode: {self.viz_mode})
Grid: {self.grid_width}x{self.grid_height}

ROBOT STATUS:
Active: {summary_stats['active']}
Picking: {summary_stats['picking']}
Jobs Done: {int(summary_stats.get('total_tasks', 0))}

PROGRESS:
Timestep: {timestep}/{self.max_timestep-1}
Progress: {timestep/self.max_timestep*100:.1f}%

WAREHOUSE:
Shelves: {self.warehouse_stats['shelves']}
Endpoints: {self.warehouse_stats['endpoints']}

Top 8 Robots:
{chr(10).join(robot_status[:8])}"""
        
        font_size = 9 if self.viz_mode == "DETAILED" else 8
        self.ax_info.text(0.1, 9.8, info_text, fontsize=font_size, ha='left', va='top',
                         fontfamily='monospace', 
                         bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcyan", alpha=0.8))

    def animate(self, frame):
        """Generalized animation function"""
        float_timestep = frame / float(self.frames_per_step)
        self.current_timestep = float_timestep
        robot_status, summary_stats = self.update_dynamic_elements(float_timestep)
        
        if self.use_info_panel:
            self.update_info_panel(float_timestep, robot_status, summary_stats)
        
        return self.agent_artists + self.trail_artists

    # Include all the previous data loading methods (load_kiva_map, load_raw_data, etc.)
    # [Previous methods remain the same - keeping the response concise]

    def generate_demo_data(self):
        """Generate demo data for any number of robots"""
        demo_data = {}
        
        # Find positions
        robot_positions = np.where(self.map_data == 'r')
        endpoint_positions = np.where(self.map_data == 'e')
        
        robot_locs = [(y * self.grid_width + x, x, y) for y, x in zip(robot_positions[0], robot_positions[1])]
        endpoint_locs = [(y * self.grid_width + x, x, y) for y, x in zip(endpoint_positions[0], endpoint_positions[1])]
        
        # **ADAPTIVE: Generate appropriate number of demo robots**
        if not robot_locs:  # If no robot positions in map, create distributed starts
            num_demo_robots = min(self.num_agents, 50) if self.num_agents > 0 else 25
        else:
            num_demo_robots = min(self.num_agents, len(robot_locs) * 3) if self.num_agents > 0 else min(25, len(robot_locs))
        
        for agent_id in range(num_demo_robots):
            # Distribute starting positions
            if robot_locs:
                start_loc, start_x, start_y = robot_locs[agent_id % len(robot_locs)]
            else:
                # Create grid distribution for many robots
                start_x = 1 + (agent_id % int(math.sqrt(self.grid_width - 2)))
                start_y = 1 + (agent_id // int(math.sqrt(self.grid_width - 2)))
                start_x = min(start_x, self.grid_width - 2)
                start_y = min(start_y, self.grid_height - 2)
            
            # Distribute goal positions
            if endpoint_locs:
                goal_loc, goal_x, goal_y = endpoint_locs[(agent_id * 7) % len(endpoint_locs)]
            else:
                goal_x = self.grid_width - 2 - (agent_id % 5)
                goal_y = self.grid_height - 2 - (agent_id // 5)
            
            # Variable path lengths for realistic movement
            base_length = 30
            variation = agent_id % 20
            path_length = base_length + variation
            
            path = []
            for t in range(path_length):
                progress = min(1.0, t / (path_length * 0.8))
                x = int(start_x + (goal_x - start_x) * progress)
                y = int(start_y + (goal_y - start_y) * progress)
                
                # Add movement variation
                if t % 3 == 0 and t > 5:
                    x += (agent_id % 3) - 1
                    y += ((agent_id + t) % 3) - 1
                    x = max(0, min(x, self.grid_width - 1))
                    y = max(0, min(y, self.grid_height - 1))
                
                location_id = y * self.grid_width + x
                path.append((location_id, t))
            
            demo_data[agent_id] = path
        
        print(f"Generated demo data for {num_demo_robots} robots")
        return demo_data

    # [Include all other methods from previous versions]
    def load_kiva_map(self, map_file):
        """Load Kiva warehouse map"""
        if not os.path.exists(map_file):
            print(f"ERROR: Map file {map_file} not found!")
            return np.array([['.' for _ in range(46)] for _ in range(33)])
        
        with open(map_file, 'r') as f:
            lines = f.readlines()
        
        try:
            header = lines[0].strip().split(',')
            map_height, map_width = int(header[0]), int(header[1])
            
            map_grid = []
            for i in range(4, 4 + map_height):
                if i < len(lines):
                    row = lines[i].strip()[:map_width].ljust(map_width, '.')
                    map_grid.append(list(row))
                else:
                    map_grid.append(['.'] * map_width)
            
            return np.array(map_grid)
            
        except Exception as e:
            print(f"Error parsing map: {e}")
            return np.array([['.' if (x+y) % 3 != 0 else '@' for x in range(46)] for y in range(33)])

    def load_raw_data(self, results_file):
        """Load RHCR results"""
        if not os.path.exists(results_file):
            print(f"WARNING: Results file {results_file} not found. Using demo data.")
            return self.generate_demo_data()
        
        try:
            with open(results_file, 'r') as f:
                lines = f.readlines()
            
            num_agents = int(lines[0].strip())
            raw_data = {}
            
            for agent_id in range(num_agents):
                if agent_id + 1 < len(lines):
                    line = lines[agent_id + 1].strip()
                    positions = line.split(';')
                    
                    agent_data = []
                    for pos in positions:
                        if pos.strip():
                            try:
                                parts = pos.split(',')
                                location_id = int(parts[0])
                                orientation = int(parts[1]) if len(parts) > 1 else 0
                                timestep = int(parts[2]) if len(parts) > 2 else int(parts[1])
                                agent_data.append((location_id, timestep, orientation))
                            except:
                                continue
                    
                    raw_data[agent_id] = sorted(agent_data, key=lambda x: x[1])
            
            return raw_data
            
        except Exception as e:
            print(f"Error loading results: {e}")
            return self.generate_demo_data()

    def load_solver_metrics(self, timestep):
        """Load metrics from solver.csv for the current timestep"""
        solver_csv = os.path.join(self.results_dir, "solver.csv")
        if not os.path.exists(solver_csv):
            return {}
            
        try:
            # We want to find the line where column 9 (Timestep) matches our frame
            df = pd.read_csv(solver_csv, header=None)
            # Find closest row to current timestep
            mask = df[9] <= timestep
            if not mask.any():
                return {}
            row = df[mask].iloc[-1]
            
            return {
                'cost': row[5],
                'min_cost': row[6],
                'nodes': row[3],
                'collisions': row[8],
                'runtime': row[0]
            }
        except Exception:
            return {}

    def load_tasks_data(self, tasks_file):
        """Load finished tasks data from tasks.txt"""
        if not tasks_file or not os.path.exists(tasks_file):
            return {}
        
        tasks_data = {}
        try:
            with open(tasks_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            num_agents = int(lines[0].strip())
            print(f"DEBUG: Loaded tasks for {num_agents} agents from {tasks_file}")
            for agent_id in range(num_agents):
                if agent_id + 1 < len(lines):
                    line = lines[agent_id + 1].strip()
                    parts = line.split(';')
                    
                    robot_tasks = []
                    for p in parts:
                        if p.strip():
                            sub = p.split(',')
                            if len(sub) >= 2:
                                loc = int(sub[0])
                                time = int(sub[1])
                                robot_tasks.append((loc, time))
                    tasks_data[agent_id] = robot_tasks
            return tasks_data
        except Exception as e:
            print(f"Error loading tasks: {e}")
            return {}

    def location_to_xy(self, location_id):
        """Convert location ID to x,y coordinates"""
        return location_id % self.grid_width, location_id // self.grid_width

    def convert_to_solution(self):
        """Convert to solution format"""
        solution = {'agents': {}}
        
        for agent_id, agent_data in self.raw_data.items():
            agent_path = []
            for location_id, timestep, orientation in agent_data:
                x, y = self.location_to_xy(location_id)
                x = max(0, min(x, self.grid_width - 1))
                y = max(0, min(y, self.grid_height - 1))
                agent_path.append((x, y, orientation))
            
            solution['agents'][agent_id] = agent_path
        
        return solution

    def run(self, show=True):
        """Start generalized visualization"""
        print(f"\nStarting Generalized Kiva Warehouse Visualization")
        # ... (rest of prints)
        print(f"Robots: {self.num_agents} | Mode: {self.viz_mode}")
        print(f"Animation: {self.animation_interval}ms intervals")
        
        mode_descriptions = {
            "DETAILED": "Full detail with individual robot tracking",
            "MEDIUM": "Simplified view with robot IDs", 
            "COMPACT": "Compact view for moderate robot counts",
            "DENSE": "Minimal detail for large robot counts",
            "HEATMAP": "Density heatmap for massive robot swarms"
        }
        
        print(f"Description: {mode_descriptions.get(self.viz_mode, 'Unknown mode')}")
        if show:
            print("Close window to exit")
        
        anim = animation.FuncAnimation(
        self.fig, self.animate, frames=self.max_timestep * self.frames_per_step,
        interval=self.animation_interval // self.frames_per_step,
            blit=False,
            repeat=True,
            cache_frame_data=False
        )
        
        plt.tight_layout()
        if show:
            plt.show()
        return anim

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--map', type=str, default='kiva.map')
    parser.add_argument('--result', type=str, default='my_results_paths.txt')
    parser.add_argument('--tasks', type=str, default=None)
    parser.add_argument('--save', type=str, default=None, help='Save animation to file (e.g. animation.gif)')
    parser.add_argument('--fp_width', type=int, default=3, help='Footprint width in cells (x-direction at theta=0)')
    parser.add_argument('--fp_height', type=int, default=1, help='Footprint height in cells (y-direction at theta=0)')
    args = parser.parse_args()

    print("=" * 70)
    print("    GENERALIZED KIVA WAREHOUSE VISUALIZER")
    print("    Automatically adapts to any number of robots")
    print("=" * 70)
    
    try:
        visualizer = GeneralizedKivaVisualizer(args.map, args.result, args.tasks)
        visualizer.fp_width = args.fp_width
        visualizer.fp_height = args.fp_height
        anim = visualizer.run(show=(args.save is None))
        if args.save:
            print(f"Saving animation to {args.save}...")
            if args.save.endswith('.gif'):
                anim.save(args.save, writer='pillow')
            else:
                anim.save(args.save, writer='ffmpeg', fps=10)
            print("Save complete.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()