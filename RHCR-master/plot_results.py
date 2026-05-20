import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

def plot_sim_results(folder_path):
    print(f"Analyzing results in: {folder_path}")
    
    solver_csv = os.path.join(folder_path, 'solver.csv')
    tasks_txt = os.path.join(folder_path, 'tasks.txt')
    
    if not os.path.exists(solver_csv):
        print("Error: solver.csv not found!")
        return

    # 1. Load Solver Data
    # Columns: Runtime, HL_exp, HL_gen, LL_exp, LL_gen, Cost, MinCost, AvgLen, Collisions, Timestep, Agents, Seed
    cols = ['Runtime', 'HL_exp', 'HL_gen', 'LL_exp', 'LL_gen', 'Cost', 'MinCost', 'AvgLen', 'Collisions', 'Timestep', 'Agents', 'Seed']
    df = pd.read_csv(solver_csv, names=cols)
    
    # 2. Extract Throughput Data from tasks.txt
    print("Parsing tasks.txt for throughput analysis...")
    all_finish_times = []
    if os.path.exists(tasks_txt):
        with open(tasks_txt, 'r') as f:
            lines = f.readlines()
            # First line is agent count
            for line in lines[1:]:
                tasks = line.strip().split(';')
                for task in tasks:
                    if not task or ',' not in task: continue
                    parts = task.split(',')
                    finish_time = int(parts[1])
                    if finish_time > 0:
                        all_finish_times.append(finish_time)
    
    all_finish_times.sort()
    
    # Calculate Cumulative Tasks
    timesteps = df['Timestep'].unique()
    cumulative_tasks = []
    for t in timesteps:
        count = sum(1 for ft in all_finish_times if ft <= t)
        cumulative_tasks.append(count)

    # CREATE PLOTS
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Plot A: Cumulative Goal Visits (Matches Paper Fig 4h)
    ax1.plot(timesteps, cumulative_tasks, color='#1f77b4', linewidth=3, label='CFNRS (Our Implementation)')
    ax1.set_title('Cumulative Goal Visits (Throughput)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Timesteps', fontsize=12)
    ax1.set_ylabel('Total Completed Tasks', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot B: Distance Optimization (Proposed vs Ideal)
    ax2.plot(df['Timestep'], df['Cost'], color='#d62728', label='Actual Path Cost', alpha=0.8)
    ax2.plot(df['Timestep'], df['MinCost'], color='#2ca02c', linestyle='--', label='Ideal (Manhattan Dist)', alpha=0.8)
    ax2.set_title('Path Optimization (Cost vs Ideal)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Timesteps', fontsize=12)
    ax2.set_ylabel('Total Steps', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    output_png = os.path.join(folder_path, 'paper_alignment_results.png')
    plt.savefig(output_png, dpi=300)
    print(f"SUCCESS: Analysis graphs saved to {output_png}")
    plt.show()

if __name__ == "__main__":
    # Default to the test_50_agents folder
    target = r"c:\Users\DILEEP\MATLAB\Projects\untitled\BTP\MAPF-with-multi-level-architecture\RHCR-master\exp\test_50_agents"
    plot_sim_results(target)
