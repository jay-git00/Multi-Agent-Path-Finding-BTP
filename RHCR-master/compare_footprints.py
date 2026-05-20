import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import argparse

def parse_tasks(tasks_txt):
    all_finish_times = []
    if os.path.exists(tasks_txt):
        with open(tasks_txt, 'r') as f:
            lines = f.readlines()
            for line in lines[1:]:
                tasks = line.strip().split(';')
                for task in tasks:
                    if not task or ',' not in task: continue
                    parts = task.split(',')
                    finish_time = int(parts[1])
                    if finish_time > 0:
                        all_finish_times.append(finish_time)
    all_finish_times.sort()
    return all_finish_times

def plot_comparison(point_folder, footprint_folder, output_file):
    print(f"Comparing {point_folder} vs {footprint_folder}")
    
    point_tasks = parse_tasks(os.path.join(point_folder, 'tasks.txt'))
    print(f"Point tasks: {len(point_tasks)}")
    footprint_tasks = parse_tasks(os.path.join(footprint_folder, 'tasks.txt'))
    print(f"Footprint tasks: {len(footprint_tasks)}")
    
    # Get max time from solver.csv
    cols = ['Runtime', 'HL_exp', 'HL_gen', 'LL_exp', 'LL_gen', 'Cost', 'MinCost', 'AvgLen', 'Collisions', 'Timestep', 'Agents', 'Seed']
    df_p = pd.read_csv(os.path.join(point_folder, 'solver.csv'), names=cols)
    df_f = pd.read_csv(os.path.join(footprint_folder, 'solver.csv'), names=cols)
    
    t_max = max(df_p['Timestep'].max(), df_f['Timestep'].max())
    timesteps = np.linspace(0, t_max, 100)
    
    cum_p = [sum(1 for ft in point_tasks if ft <= t) for t in timesteps]
    cum_f = [sum(1 for ft in footprint_tasks if ft <= t) for t in timesteps]
    
    plt.figure(figsize=(10, 6))
    plt.plot(timesteps, cum_p, 'r-', label='Point Agents (1x1)', linewidth=2)
    plt.plot(timesteps, cum_f, 'b-', label='Footprint-Aware Agents (3x3)', linewidth=2)
    
    plt.title('Throughput Comparison: Point vs Footprint-Aware MAPF', fontsize=14)
    plt.xlabel('Timestep', fontsize=12)
    plt.ylabel('Cumulative Tasks Completed', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig(output_file, dpi=300)
    print(f"Saved comparison plot to {output_file}")
    plt.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--point', type=str, required=True)
    parser.add_argument('--footprint', type=str, required=True)
    parser.add_argument('--out', type=str, default='comparison_results.png')
    args = parser.parse_args()
    
    plot_comparison(args.point, args.footprint, args.out)
