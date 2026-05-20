import matplotlib
matplotlib.use('Agg') # Headless backend
import matplotlib.pyplot as plt
from mapf_visualizer import GeneralizedKivaVisualizer
import os

def run():
    print("Initializing Visualizer (Headless)...")
    # Paths relative to RHCR-master
    map_file = os.path.join("maps", "kiva.map")
    results_file = os.path.join("exp", "test", "paths.txt")
    
    output_file = "simulation.gif"
    
    if not os.path.exists(map_file):
        print(f"Map file not found: {map_file}")
        return
    if not os.path.exists(results_file):
        print(f"Results file not found: {results_file}")
        return

    viz = GeneralizedKivaVisualizer(map_file, results_file)
    
    print(f"Generating animation for {viz.num_agents} agents...")
    
    # We need to manually construct the animation object since viz.run() calls plt.show()
    # Copying logic from viz.run() but replacing plt.show() with save
    
    print(f"Robots: {viz.num_agents} | Mode: {viz.viz_mode}")
    
    anim = matplotlib.animation.FuncAnimation(
        viz.fig, viz.animate, frames=viz.max_timestep,
        interval=viz.animation_interval,
        blit=False,
        repeat=True
    )
    
    print(f"Saving to {output_file}...")
    anim.save(output_file, writer='pillow', fps=10)
    print(f"Done! Saved to {output_file}")

if __name__ == "__main__":
    run()
