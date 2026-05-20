from mapf_visualizer import GeneralizedKivaVisualizer
import os

def run_baseline():
    print("Initializing BASELINE Visualizer (Seniors' Code)...")
    map_file = os.path.join("maps", "kiva.map")
    results_file = os.path.join("exp", "seniors_50_agents", "paths.txt")
    tasks_file = os.path.join("exp", "seniors_50_agents", "tasks.txt")
    
    if not os.path.exists(results_file):
        print(f"ERROR: Baseline results not found at {results_file}")
        return

    viz = GeneralizedKivaVisualizer(map_file, results_file, tasks_file)
    print(f"Loaded {viz.num_agents} bots from BASELINE simulation.")
    viz.run()

if __name__ == "__main__":
    run_baseline()
