import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

fig, ax = plt.subplots(figsize=(16, 4))
ax.set_xlim(0, 42)
ax.set_ylim(0, 14)
ax.axis("off")

# COLORS
yellow = '#F9C349'
red = '#A84F4F'
robot_color = '#5A2D82'

# -------------------------
# LEFT ZONE (with padding)
# -------------------------
left_x = 1       # left padding
left_w = 18      # width including padding

# background white padding
ax.add_patch(Rectangle((left_x-1, 1), left_w+2, 12, facecolor="white"))

# yellow area
ax.add_patch(Rectangle((left_x, 9), left_w, 4, facecolor=yellow))
ax.add_patch(Rectangle((left_x, 6), left_w, 3, facecolor=red))
ax.add_patch(Rectangle((left_x, 1), left_w, 5, facecolor=yellow))

# -------------------------
# RIGHT ZONE (with padding)
# -------------------------
right_x = 23
right_w = 18

# background white padding
ax.add_patch(Rectangle((right_x-1, 1), right_w+2, 12, facecolor="white"))

# yellow/red/yellow stripes
ax.add_patch(Rectangle((right_x, 9), right_w, 4, facecolor=yellow))
ax.add_patch(Rectangle((right_x, 6), right_w, 3, facecolor=red))
ax.add_patch(Rectangle((right_x, 1), right_w, 5, facecolor=yellow))

# -------------------------
# ROBOTS & ARROW
# -------------------------

# robot positions
left_robot_x = left_x + 17
right_robot_positions = [
    right_x + 3,
    right_x + 8,
    right_x + 13
]

# draw left robot
ax.add_patch(Circle((left_robot_x, 3), 0.8, facecolor=robot_color,
                    edgecolor='black', linewidth=1.5))

# arrow →


# draw right robots (3)
for px in right_robot_positions:
    ax.add_patch(Circle((px, 3), 0.8, facecolor=robot_color,
                        edgecolor='black', linewidth=1.5))

plt.tight_layout()
plt.show()
