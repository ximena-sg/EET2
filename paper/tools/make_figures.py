"""Generate the two figures for the RCES paper."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = "/tmp/claude-0/-home-user-EET2/4087ed32-f26b-5eca-a22f-9c8dab09c6f8/scratchpad"

LAYER_FC = "#eef3fa"
LAYER_EC = "#3a5a8c"
BOX_FC = "#ffffff"
BOX_EC = "#3a5a8c"


def box(ax, x, y, w, h, text, fc=BOX_FC, ec=BOX_EC, fs=8.5, bold=False, rounded=True):
    style = "round,pad=0.02,rounding_size=0.06" if rounded else "square,pad=0.02"
    p = FancyBboxPatch((x, y), w, h, boxstyle=style, fc=fc, ec=ec, lw=1.1)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", wrap=True)
    return p


def arrow(ax, x1, y1, x2, y2, style="-|>", ls="-"):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=12,
                        lw=1.1, color="#333333", linestyle=ls)
    ax.add_patch(a)


# ---------------- Figure 1: five-layer architecture ----------------
fig, ax = plt.subplots(figsize=(7.0, 8.4))
ax.set_xlim(0, 10)
ax.set_ylim(0, 21.5)
ax.axis("off")

def layer(ax, y, h, title):
    p = FancyBboxPatch((0.3, y), 9.4, h, boxstyle="round,pad=0.02,rounding_size=0.1",
                       fc=LAYER_FC, ec=LAYER_EC, lw=1.4)
    ax.add_patch(p)
    ax.text(0.55, y + h - 0.38, title, ha="left", va="center", fontsize=9.5,
            fontweight="bold", color="#1f3a63")

# Layer 1 (top): Definition & Inventory
layer(ax, 18.4, 2.9, "Layer 1 — Definition and Inventory")
box(ax, 0.8, 18.7, 2.6, 1.6, "inventory.yaml\n(nodes, roles,\ntopology)")
box(ax, 3.7, 18.7, 2.6, 1.6, "Protected .env\n(secrets and\naccess data)")
box(ax, 6.6, 18.7, 2.8, 1.6, "Round-trip\ninventory engine")
arrow(ax, 3.4, 19.2, 6.6, 19.0)
arrow(ax, 6.3, 19.5, 6.6, 19.5)

# Layer 2: Orchestration
layer(ax, 14.9, 2.9, "Layer 2 — Orchestration and Connectivity")
box(ax, 0.8, 15.2, 2.6, 1.6, "Central\ncollector")
box(ax, 3.7, 15.2, 2.6, 1.6, "Credential\nquarantine\n(anti-lockout)")
box(ax, 6.6, 15.2, 2.8, 1.6, "Driver\ndispatcher")
arrow(ax, 3.4, 16.0, 3.7, 16.0, style="<|-|>")
arrow(ax, 3.4, 16.0 - 0.001, 3.4, 16.0)
arrow(ax, 6.3, 16.0, 6.6, 16.0)
arrow(ax, 8.0, 18.7, 8.0, 16.8)   # inventory engine -> dispatcher col
arrow(ax, 2.1, 18.7, 2.1, 16.8)   # inventory -> collector

# Layer 3: Hardware abstraction
layer(ax, 11.0, 3.3, "Layer 3 — Hardware Abstraction (device drivers)")
names = ["Dell\nPC7000/\nPC3500", "Comware\nOS 5.20", "Cisco IOS/\nIOS-XE", "MikroTik\nRouterOS", "TP-Link\nJetStream/ER"]
xs = [0.8, 2.6, 4.4, 6.2, 8.0]
for x, n in zip(xs, names):
    box(ax, x, 11.9, 1.55, 1.5, n, fs=7.3)
box(ax, 2.6, 11.15, 4.8, 0.62, "ssh_compat — temporary promotion of legacy ciphers", fs=7.6)
arrow(ax, 8.0, 15.2, 8.0, 13.4)   # dispatcher -> drivers

# Layer 4: Integrity & versioning
layer(ax, 7.6, 2.85, "Layer 4 — Integrity and Versioning")
box(ax, 0.8, 7.9, 4.1, 1.6, "Volatile-pattern filter and\nend-of-file integrity\nvalidation")
box(ax, 5.4, 7.9, 4.0, 1.6, "GitStore engine\n(transactional commits,\nfilesystem locks)")
arrow(ax, 4.9, 8.7, 5.4, 8.7)
arrow(ax, 2.85, 11.0, 2.85, 9.5)

# Layer 5: Analysis & presentation
layer(ax, 3.0, 4.1, "Layer 5 — Analysis and Presentation")
box(ax, 0.8, 5.15, 4.1, 1.35, "Side-by-side diff engine\n(word-level tokenization)")
box(ax, 5.4, 5.15, 4.0, 1.35, "Topology inference and\nfindings engine")
box(ax, 0.8, 3.3, 4.1, 1.3, "Native SPA web interface")
box(ax, 5.4, 3.3, 4.0, 1.3, "Command-line console (CLI)")
arrow(ax, 7.4, 7.9, 7.4, 6.5)
arrow(ax, 2.85, 7.9, 2.85, 6.5)
arrow(ax, 2.85, 5.15, 2.85, 4.6)
arrow(ax, 7.4, 5.15, 7.4, 4.6)

plt.tight_layout()
plt.savefig(f"{OUT}/figure1_architecture.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# ---------------- Figure 2: collection workflow with quarantine ----------------
fig, ax = plt.subplots(figsize=(7.2, 4.6))
ax.set_xlim(0, 12)
ax.set_ylim(0, 7.5)
ax.axis("off")

steps = [
    (0.3, 5.6, "1. Load inventory\nand credentials"),
    (3.35, 5.6, "2. Quarantine check\n(credential enabled?)"),
    (6.4, 5.6, "3. Adaptive SSH\nsession (driver +\nssh_compat)"),
    (9.45, 5.6, "4. Paging disabled,\nprivilege elevation,\nfull dump"),
    (9.45, 2.6, "5. Volatile-pattern\nfilter + end-of-file\nvalidation"),
    (6.4, 2.6, "6. Transactional\ncommit (GitStore)"),
    (3.35, 2.6, "7. Diff and topology\nanalysis"),
    (0.3, 2.6, "8. Web SPA / CLI\nreporting"),
]
for x, y, t in steps:
    box(ax, x, y, 2.35, 1.45, t, fs=7.8)

arrow(ax, 2.65, 6.32, 3.35, 6.32)
arrow(ax, 5.7, 6.32, 6.4, 6.32)
arrow(ax, 8.75, 6.32, 9.45, 6.32)
arrow(ax, 10.6, 5.6, 10.6, 4.05)
arrow(ax, 9.45, 3.32, 8.75, 3.32)
arrow(ax, 6.4, 3.32, 5.7, 3.32)
arrow(ax, 3.35, 3.32, 2.65, 3.32)

# failure branch
box(ax, 3.35, 0.35, 5.4, 1.2, "Two consecutive authentication failures →\ncredential quarantined on all linked nodes", fc="#fdeeee", ec="#a33", fs=7.8)
arrow(ax, 7.6, 5.6, 6.05, 1.55, ls="--")
ax.text(6.5, 4.0, "auth.\nfailure", fontsize=7.2, color="#a33", ha="center")

# reject branch
ax.text(11.4, 4.8, "truncated dump\n→ rejected", fontsize=7.2, color="#a33", ha="center")

plt.tight_layout()
plt.savefig(f"{OUT}/figure2_workflow.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print("figures done")
