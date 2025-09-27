
"""
Discordance Share — 4× Donut (AmbQ & GoldX with overlap)
Reproduces the v5 figure with:
- Four donut charts (one per method), using categories:
  GoldX only, AmbQ only, AmbQ ∩ GoldX, Others.
- Percent labels outside the ring.
- Single global legend.
- Method names at the bottom, big title at the top.
- Colors are colorblind-friendly; overlap wedge uses hatch.

Usage:
    python discordance_share_plot.py
Outputs:
    - tile_v5_<method>.png  (4 tiles)
    - legend_discordance_share_v5.png (legend image)
    - discordance_share_4_donuts_goldx_single_legend_v5.png (final composite)
"""

import os
from typing import Tuple, List

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from PIL import Image, ImageDraw, ImageFont

# =====================
# Data (Discordance Share, in %)
# =====================
ROWS = [
    {"Method": "Opensearch",     "GF_share": 46.24, "AmbQ_share": 15.05, "Overall_share": 58.06},
    {"Method": "Alpha-SQL-32B",  "GF_share": 51.14, "AmbQ_share": 11.36, "Overall_share": 57.95},
    {"Method": "RSL-SQL",        "GF_share": 53.01, "AmbQ_share": 18.07, "Overall_share": 63.86},
    {"Method": "OmniSQL-32B",    "GF_share": 44.19, "AmbQ_share": 13.95, "Overall_share": 54.65},
]

# =====================
# Config (fonts & layout)
# =====================
TITLE_TEXT   = "Discordance Share"
TITLE_SIZE   = 120  # big title at top (increased)
METHOD_SIZE  = 32   # method name under each donut (increased)
CENTER_SIZE  = 34   # center label "AmbQ + GoldX" (increased)
PCT_SIZE     = 26   # slice percentage labels (outside) (increased)
LEGEND_SIZE  = 32   # legend text size (same as method title)

DONUT_WIDTH  = 0.4  # thinner ring -> larger hole
LABEL_DIST   = 1.10 # percentage label distance (outside the ring)

# Colorblind-friendly palette
COLOR_GOLDX = "#4C78A8"   # blue
COLOR_AMBQ  = "#F58518"   # orange
COLOR_BOTH  = "#54A24B"   # green (hatch)
COLOR_OTH   = "#B9B9B9"   # gray
COLORS = [COLOR_GOLDX, COLOR_AMBQ, COLOR_BOTH, COLOR_OTH]

OUTDIR = "figure"  # output to figure folder

# =====================
# Helpers
# =====================
def decompose_shares(gf: float, amb: float, overall: float) -> Tuple[float, float, float, float]:
    """
    Given:
        gf:    Discordance Share attributed to GoldX (union-based)
        amb:   Discordance Share attributed to AmbQ (union-based)
        overall: Share of samples that fall in (AmbQ ∪ GoldX)
    Returns (GoldX only, AmbQ only, Both, Others) as percentages that sum to ~100.
    Uses the identity: |A ∩ B| = |A| + |B| − |A ∪ B|.
    """
    both = max(0.0, gf + amb - overall)
    gf_only = max(0.0, gf - both)
    amb_only = max(0.0, amb - both)
    others = max(0.0, 100.0 - overall)
    s = gf_only + amb_only + both + others
    if s > 0:
        k = 100.0 / s
        gf_only, amb_only, both, others = [v * k for v in (gf_only, amb_only, both, others)]
    return gf_only, amb_only, both, others

def make_donut_tile(method: str, gf: float, amb: float, overall: float, out_path: str) -> str:
    """Create one donut chart PNG with bottom method label; return saved path."""
    gf_only, amb_only, both, others = decompose_shares(gf, amb, overall)
    values = [gf_only, amb_only, both, others]
    pct_labels = [f"{v:.1f}%" for v in values]

    # Slightly wider figure; expand margins to avoid clipping outer labels
    fig = plt.figure(figsize=(9.5, 9.0), dpi=180)
    # axes: [left, bottom, width, height]
    ax = fig.add_axes([0.12, 0.15, 0.76, 0.80])
    wedges, *_ = ax.pie(
        values,
        labels=pct_labels,           # outside percentages
        labeldistance=LABEL_DIST,    # distance from center ( > 1 means outside )
        startangle=90,
        textprops={"fontsize": PCT_SIZE},
        wedgeprops=dict(width=DONUT_WIDTH),
        colors=COLORS
    )
    # Hatch only the intersection wedge
    wedges[2].set_hatch("//")
    ax.axis('equal')

    # Center label (union = AmbQ + GoldX)
    ax.text(0, 0, f"AmbQ + GoldX\n{overall:.1f}%", ha='center', va='center', fontsize=CENTER_SIZE)

    # Method label at bottom - moved further down
    fig.text(0.5, 0.08, method, ha='center', va='center', fontsize=METHOD_SIZE)

    fig.savefig(out_path) 
    plt.close(fig)
    return out_path

def build_legend(path: str) -> str:
    """Create a single legend image with succinct labels; return path."""
    handles = [
        Patch(facecolor=COLOR_GOLDX, label="GoldX"),
        Patch(facecolor=COLOR_AMBQ,  label="AmbQ"),
        Patch(facecolor=COLOR_BOTH,  label="AmbQ ∩ GoldX", hatch="//"),
        Patch(facecolor=COLOR_OTH,   label="Others"),
    ]
    fig = plt.figure(figsize=(8.8, 1.0), dpi=180)
    fig.legend(
        handles=handles, loc="center", ncol=4, frameon=False,
        handlelength=2.0, handleheight=1.0, borderpad=0.1, labelspacing=0.8, fontsize=LEGEND_SIZE
    )
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(path, transparent=True, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    return path

def compose_canvas(tile_paths: List[str], legend_path: str, out_path: str) -> str:
    """Compose 2×2 grid + title + single legend into the final PNG."""
    tiles = [Image.open(p).convert("RGBA") for p in tile_paths]
    w, h = tiles[0].size  # all tiles same size

    legend_img = Image.open(legend_path).convert("RGBA")
    legend_w, legend_h = legend_img.size

    cols, rows_n = 2, 2

    # No title, start from top
    title_h = 0

    canvas_w = cols * w + 200  # reduced horizontal spacing for centering
    canvas_h = rows_n * h + title_h + (legend_h + 26) - 40  # reduced vertical spacing
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    # No title to draw

    # Paste tiles with centered positioning and slightly increased vertical spacing
    horizontal_offset = 50  # center the donuts horizontally
    vertical_spacing = 80  # slightly increased spacing between rows
    positions = [(horizontal_offset, title_h), (horizontal_offset + w + 30, title_h), 
                 (horizontal_offset, title_h + h - vertical_spacing), (horizontal_offset + w + 30, title_h + h - vertical_spacing)]
    for im, pos in zip(tiles, positions):
        canvas.paste(im, pos)

    # Paste legend centered at bottom - greatly reduced distance from donuts
    legend_x = (canvas_w - legend_w) // 2
    legend_y = title_h + rows_n * h - 60
    canvas.paste(legend_img, (legend_x, legend_y), legend_img)

    # Save as PNG first
    png_path = out_path.replace('.pdf', '.png')
    canvas.save(png_path)
    
    # Convert PNG to PDF using Pillow
    from PIL import Image as PILImage
    img = PILImage.open(png_path)
    img.save(out_path, "PDF")
    
    # Keep PNG file (don't delete it)
    print(f"Saved PNG to: {png_path}")
    print(f"Saved PDF to: {out_path}")
    
    return out_path

def main():
    # Build donut tiles (temporary files)
    tile_paths = []
    for row in ROWS:
        out = os.path.join(OUTDIR, f"tile_v5_{row['Method'].replace(' ', '_').replace('/', '-')}.png")
        tile_paths.append(make_donut_tile(row["Method"], row["GF_share"], row["AmbQ_share"], row["Overall_share"], out))

    # Build legend (temporary file)
    legend_path = os.path.join(OUTDIR, "legend_discordance_share_v5.png")
    build_legend(legend_path)

    # Compose final canvas
    final_path = os.path.join(OUTDIR, "discordance.pdf")
    compose_canvas(tile_paths, legend_path, final_path)
    
    # Clean up temporary files
    for tile_path in tile_paths:
        if os.path.exists(tile_path):
            os.remove(tile_path)
    if os.path.exists(legend_path):
        os.remove(legend_path)
    
    print(f"Saved figure to: {final_path}")

if __name__ == "__main__":
    main()
