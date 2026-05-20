import matplotlib.pyplot as plt
from mapf_visualizer import GeneralizedKivaVisualizer
import os
import sys

def run():
    print("Initializing LIVE Visualizer...")
    print("NOTE: This will open a popup window. Please check your taskbar if you don't see it.")
    
    # Paths relative to RHCR-master
    map_file = os.path.join("maps", "kiva.map")
    results_file = os.path.join("exp", "test_50_agents", "paths.txt")
    tasks_file = os.path.join("exp", "test_50_agents", "tasks.txt")
    
    print(f"DEBUG: Loading MAP: {os.path.abspath(map_file)}")
    print(f"DEBUG: Loading PATHS: {os.path.abspath(results_file)}")
    print(f"DEBUG: Loading TASKS: {os.path.abspath(tasks_file)}")

    if not os.path.exists(map_file):
        print(f"ERROR: Map file not found: {map_file}")
        return
    if not os.path.exists(results_file):
        print(f"ERROR: Results file not found: {results_file}")
        return

    # Initialize visualizer with correct paths
    viz = GeneralizedKivaVisualizer(map_file, results_file, tasks_file)
    
    print(f"Loaded {viz.num_agents} agents.")
    print("Launching window...")
    
    # Run the interactive visualizer
    viz.run()

if __name__ == "__main__":
    run()
