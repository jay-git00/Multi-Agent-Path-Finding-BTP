import matplotlib.pyplot as plt
from mapf_visualizer import GeneralizedKivaVisualizer
import os

def run():
    print("Initializing LIVE Visualizer for Kinematic Map...")
    
    map_file = os.path.join("maps", "kiva_kinematic.map")
    results_file = os.path.join("exp", "kinematic_test", "paths.txt")
    tasks_file = os.path.join("exp", "kinematic_test", "tasks.txt")
    
    if not os.path.exists(results_file):
        print(f"ERROR: Results file not found: {results_file}")
        return

    viz = GeneralizedKivaVisualizer(map_file, results_file, tasks_file)
    # Set the footprint size visually
    viz.agent_shape = 'rect'
    viz.agent_width = 1
    viz.agent_length = 3
    
    print(f"Loaded {viz.num_agents} agents.")
    print("Launching window... Please check your taskbar!")
    viz.run()

if __name__ == "__main__":
    run()
