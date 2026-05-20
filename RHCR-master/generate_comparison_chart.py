import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Benchmark Data
# Format: (agents, footprint, tasks_completed, throughput)
data = [
    (10, "1×1 (Point)", 117, 0.389),
    (10, "3×3 (Large)",  108, 0.359),
    (20, "1×1 (Point)", 230, 0.764),
    (20, "3×3 (Large)",   0, 0.0),   # Crashed — can't even start
]

# Chart 1: Throughput Comparison
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle("MAPF Warehouse: Point Agent vs Large Footprint Robot", 
             fontsize=16, fontweight='bold', y=0.98)

# --- Bar chart: Throughput ---
ax1 = axes[0]
agents = [10, 20]
point_tp = [0.389, 0.764]
large_tp = [0.359, 0.0]

x = np.arange(len(agents))
width = 0.35

bars1 = ax1.bar(x - width/2, point_tp, width, label='1×1 Point Agent', color='#42A5F5', edgecolor='#1565C0')
bars2 = ax1.bar(x + width/2, large_tp, width, label='3×3 Large Footprint', color='#FF7043', edgecolor='#BF360C')

ax1.set_xlabel('Number of Agents', fontsize=12)
ax1.set_ylabel('Throughput (tasks/timestep)', fontsize=12)
ax1.set_title('Throughput Comparison', fontsize=14)
ax1.set_xticks(x)
ax1.set_xticklabels(agents)
ax1.legend()
ax1.grid(axis='y', alpha=0.3)

# Add value labels on bars
for bar in bars1:
    height = bar.get_height()
    ax1.annotate(f'{height:.3f}', xy=(bar.get_x() + bar.get_width()/2, height),
                xytext=(0, 3), textcoords="offset points", ha='center', fontsize=10)
for bar in bars2:
    height = bar.get_height()
    label = f'{height:.3f}' if height > 0 else 'CRASHED'
    ax1.annotate(label, xy=(bar.get_x() + bar.get_width()/2, max(height, 0.02)),
                xytext=(0, 3), textcoords="offset points", ha='center', fontsize=10,
                color='red' if height == 0 else 'black')

# --- Bar chart: Tasks Completed ---
ax2 = axes[1]
point_tasks = [117, 230]
large_tasks = [108, 0]

bars3 = ax2.bar(x - width/2, point_tasks, width, label='1×1 Point Agent', color='#42A5F5', edgecolor='#1565C0')
bars4 = ax2.bar(x + width/2, large_tasks, width, label='3×3 Large Footprint', color='#FF7043', edgecolor='#BF360C')

ax2.set_xlabel('Number of Agents', fontsize=12)
ax2.set_ylabel('Total Tasks Completed (300 timesteps)', fontsize=12)
ax2.set_title('Task Completion Comparison', fontsize=14)
ax2.set_xticks(x)
ax2.set_xticklabels(agents)
ax2.legend()
ax2.grid(axis='y', alpha=0.3)

for bar in bars3:
    height = bar.get_height()
    ax2.annotate(f'{int(height)}', xy=(bar.get_x() + bar.get_width()/2, height),
                xytext=(0, 3), textcoords="offset points", ha='center', fontsize=10)
for bar in bars4:
    height = bar.get_height()
    label = str(int(height)) if height > 0 else 'CRASHED\n(overlap at start)'
    ax2.annotate(label, xy=(bar.get_x() + bar.get_width()/2, max(height, 5)),
                xytext=(0, 3), textcoords="offset points", ha='center', fontsize=9,
                color='red' if height == 0 else 'black')

plt.tight_layout()
output_path = r'C:\Users\DILEEP\.gemini\antigravity\brain\865483a2-de36-407d-b9b3-50b99c101f76\benchmark_comparison.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"Chart saved to {output_path}")
