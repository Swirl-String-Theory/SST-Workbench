import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Set up figure size (in inches)
fig_width = 8.0139
fig_height = 6.2739
fig = plt.figure(figsize=(fig_width, fig_height))
ax = fig.add_axes([0, 0, 1, 1])  # Use full canvas (margin=0)

# Background
ax.set_facecolor("white")

# Pseudo-space domain
for i in range(5):
    y_start = i * 1.2
    ax.add_patch(patches.Rectangle((0, y_start), 4, 1, color='orange', alpha=0.6, label='Plateau x1' if i == 0 else ""))
    ax.add_patch(patches.Rectangle((4, y_start), 4, 1, color='purple', alpha=0.4, label='Plateau x2' if i == 0 else ""))
    ax.plot([4, 4], [y_start, y_start + 1], 'k--')  # Domain wall
    ax.arrow(4, y_start + 0.5, 0.3, 0, head_width=0.1, head_length=0.1, fc='red', ec='red')

# Axes labels
ax.set_xlim(0, 8)
ax.set_ylim(0, 6)
ax.set_xticks([0, 2, 4, 6, 8])
ax.set_yticks([0, 2, 4, 6])
ax.set_xlabel("Pseudo-space σ ∈ [0, τ]", fontsize=14)
ax.set_ylabel("Slow Time nτ", fontsize=14)

# Inset ring sketch
circle = patches.Circle((7.2, 1.2), 0.6, linewidth=1, edgecolor='gray', facecolor='none', linestyle='dashed')
ax.add_patch(circle)
ax.text(7.2, 1.2, "Circulating\nField", color='gray', ha='center', va='center', fontsize=8)

# Hide top and right spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Title
ax.set_title("Delay-Induced Pattern Formation in Nonlinear Ring Systems", fontsize=14, pad=20)

# Legend
handles, labels = ax.get_legend_handles_labels()
by_label = dict(zip(labels, handles))
ax.legend(by_label.values(), by_label.keys(), loc='upper left', fontsize=10)

plt.tight_layout()
plt.show()