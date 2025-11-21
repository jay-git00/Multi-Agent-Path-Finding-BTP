import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline

# Windows (same for all k)
windows = np.array([2, 5, 10, 20, 50, 100, 200, 500])

# RAW DATA × 1000
capacity = {
    20: np.array([1.498, 1.672, 1.19, 1.19, 1.22, 1.23, 1.23, 1.23]) * 1000,
    30: np.array([2.138, 2.256, 1.68, 1.704, 1.74, 1.696, 1.696, 1.696]) * 1000,
    40: np.array([2.756, 2.855, 2.763, 2.857, 2.827, 2.827, 2.837, 2.862]) * 1000,
   
}

colors = ['royalblue', 'seagreen', 'darkorange', 'crimson']

plt.figure(figsize=(7,5))

# ---------- RAW TASKS COMPLETED ----------
for (k, y), color in zip(capacity.items(), colors):
    x_smooth = np.linspace(windows.min(), windows.max(), 300)
    y_smooth = make_interp_spline(windows, y, k=2)(x_smooth)

    plt.plot(x_smooth, y_smooth, color=color, lw=2.3, label=f'k={k}')
    plt.scatter(windows, y, color=color, marker='s', edgecolor='black')

plt.xscale("log")

# --- FIXED TICKS ---
plt.xticks([2, 5, 10, 20, 50, 100, 200, 500],
           ['2', '5', '10', '20', '50', '100', '200', '500'])

plt.xlabel("Planning Window (w)")
plt.ylabel("Tasks Completed")
plt.title("Capacity Model — Tasks Completed (×1000)")
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()

plt.tight_layout()
plt.show()
