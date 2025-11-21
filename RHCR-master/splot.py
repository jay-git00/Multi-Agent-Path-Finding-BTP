import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline

windows = np.array([2, 5, 10, 20, 50, 100, 200, 500])

# RAW DATA × 1000 (Normal Model)
normal = {
    20: np.array([0.81, 0.83, 0.86, 0.8, 0.8, 0.8, 0.8, 0.8]) * 1000,
    30: np.array([1.151, 1.198, 1.201, 1.215, 1.165, 1.168, 1.16, 1.16]) * 1000,
    40: np.array([1.547, 1.551, 1.526, 1.556, 1.556, 1.556, 1.556, 1.556]) * 1000,
    50: np.array([1.438, 1.857, 1.91, 1.923, 1.923, 1.918, 1.918, 1.918]) * 1000,
}

colors = ['royalblue', 'seagreen', 'darkorange', 'crimson']

plt.figure(figsize=(7,5))

# ---------- RAW TASKS COMPLETED ----------
for (k, y), color in zip(normal.items(), colors):
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
plt.title("Normal Model — Tasks Completed (×1000)")
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()

plt.tight_layout()
plt.show()
