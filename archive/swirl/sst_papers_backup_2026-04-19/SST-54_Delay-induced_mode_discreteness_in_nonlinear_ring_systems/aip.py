import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, FancyArrowPatch

# --- AIP exact size ---
W, H = 8.0139, 6.2739
DPI = 300

fig = plt.figure(figsize=(W, H), dpi=DPI)
ax = fig.add_axes([0,0,1,1])
ax.set_xlim(0,1)
ax.set_ylim(0,1)
ax.axis("off")

# Background
ax.add_patch(Rectangle((0,0),1,1,facecolor=(0,0,0,0.02)))

# --- LEFT: ring ---
cx, cy, R = 0.28, 0.55, 0.17
ax.add_patch(Circle((cx,cy),R,fill=False,linewidth=3,alpha=0.7))

# arrows (fixed positions, no loops)
arrows = [(0.28,0.72,0.32,0.75),(0.40,0.55,0.43,0.51),
          (0.28,0.38,0.24,0.35),(0.16,0.55,0.13,0.59)]
for x0,y0,x1,y1 in arrows:
    ax.add_patch(FancyArrowPatch((x0,y0),(x1,y1),
                                 arrowstyle='-|>',linewidth=1.5,mutation_scale=18,alpha=0.6))

ax.text(cx+0.23,cy,"delay\n$\\tau$",fontsize=18,ha="center",va="center")
ax.text(0.06,0.92,"Nonlinear ring with delay feedback",
        fontsize=22,weight="bold",alpha=0.8)
ax.text(0.06,0.87,
        r"$\epsilon \dot{x}(t)=-x(t)+\mu x(t-\tau)-x^3(t-\tau)$",
        fontsize=18,alpha=0.75)

ax.add_patch(Rectangle((0.18,0.33),0.08,0.05,facecolor=(0,0,0,0.7)))
ax.text(0.22,0.355,r"$f(\cdot)$",color="white",fontsize=16,
        ha="center",va="center")

# --- RIGHT: pseudo-space map ---
ax.add_patch(Rectangle((0.55,0.18),0.40,0.65,
                       facecolor="white",edgecolor=(0,0,0,0.6),linewidth=1.5))

bands_y = [0.22,0.27,0.32,0.37,0.42,0.47,0.52,0.57,0.62,0.67]
for i,y in enumerate(bands_y):
    shade = 0.10 if i%2==0 else 0.04
    ax.add_patch(Rectangle((0.59,y),0.32,0.04,
                           facecolor=(0,0,0,shade)))

fronts = [(0.67,0.26),(0.69,0.33),(0.71,0.40),(0.73,0.47),(0.75,0.54)]
for x,y in fronts:
    ax.plot([x,x+0.03],[y,y+0.04],linewidth=3,alpha=0.55)

ax.text(0.55,0.87,"Long-delay: pseudo-space pattern selection",
        fontsize=22,weight="bold",alpha=0.8)
ax.text(0.70,0.78,r"plateau states $x_1,x_2$",fontsize=16)
ax.text(0.95,0.20,r"$\sigma\in[0,\tau]$",fontsize=16,ha="right")
ax.text(0.52,0.50,r"$n$",fontsize=18,rotation=90)

ax.add_patch(FancyArrowPatch((0.48,0.55),(0.54,0.55),
                             arrowstyle='-|>',linewidth=2.5,
                             mutation_scale=25,alpha=0.6))
ax.text(0.51,0.59,"long-delay\nmapping",fontsize=14,ha="center")

# Bottom line
ax.text(0.05,0.06,
        "Delay-induced pattern formation yields effectively discrete circulation modes",
        fontsize=18,style="italic",alpha=0.75)

# Export
fig.savefig("AIP_highlight.tif",dpi=DPI,
            pil_kwargs={"compression":"tiff_lzw"})
plt.close(fig)