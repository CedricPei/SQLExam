
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ===============================
# Data (from your table)
# ===============================
data = [
    ("Opensearch", "Sep 2024", "DeepSeek-Chat", 77.94, 91.18, 69.78, 80.44, 56.25, 67.71, 69.37, 80.96),
    ("CSC-SQL-32B", "May 2025", "FT (XiYan-32B)", 85.00, 87.14, 71.99, 77.54, 53.06, 67.35, 71.52, 78.27),
    ("Alpha-SQL-32B", "Feb 2025", "Qwen2.5 Coder 32B", 81.02, 91.24, 69.47, 79.65, 52.58, 70.10, 69.35, 81.09),
    ("RSL-SQL", "Oct 2024", "GPT-4o", 80.15, 91.18, 64.60, 80.09, 53.61, 73.20, 66.88, 81.92),
    ("RSL-SQL", "Oct 2024", "DeepSeek-Chat", 74.29, 86.43, 59.83, 71.79, 52.04, 62.24, 62.50, 74.15),
    ("SuperSQL", "Jul 2024", "GPT-4", 67.65, 72.79, 48.66, 69.38, 45.83, 48.96, 53.73, 61.18),
    ("CodeS-15B", "Feb 2024", "FT (StarCoder)", 64.96, 67.15, 46.90, 44.69, 39.13, 32.61, 50.77, 49.01),
    ("OmniSQL-32B", "Mar 2025", "FT (Qwen2.5 Coder)", 80.00, 86.43, 67.23, 78.30, 57.14, 72.45, 68.92, 79.49),
    ("DAIL-SQL", "Nov 2023", "GPT-4", 62.50, 72.06, 44.64, 52.68, 38.95, 38.95, 48.79, 55.60),
    ("TA-SQL", "May 2024", "GPT-4o", 66.67, 71.74, 49.05, 54.66, 33.67, 44.90, 51.06, 57.63),
    ("CHESS-V1", "May 2024", "Mixed", 70.50, 70.50, 58.20, 62.87, 45.92, 48.98, 59.28, 62.24),  # treat as FT
    ("CoT", "Mar 2023", "GPT-3.5", 42.65, 50.00, 21.05, 28.07, 13.54, 19.79, 25.87, 32.83),
    ("C3-SQL", "Jul 2023", "GPT-3.5", 61.03, 62.50, 36.89, 43.11, 28.87, 30.93, 42.36, 46.29),
    ("RESD SQL-3B", "Feb 2023", "FT (T5)", 56.30, 54.07, 31.44, 31.00, 17.71, 15.62, 35.87, 34.57),
]
cols = ["method","date_str","model","simple_ex","simple_ra","moderate_ex","moderate_ra",
        "challenge_ex","challenge_ra","overall_ex","overall_ra"]
df = pd.DataFrame(data, columns=cols)
df["date"] = pd.to_datetime(df["date_str"])

# CHESS-V1 is considered finetuned for this analysis.
df["is_ft"] = df["model"].str.contains("FT", case=False, na=False) | (df["method"] == "CHESS-V1")

# Compute RA−EX deltas
for level in ["simple","moderate","challenge","overall"]:
    df[f"{level}_delta"] = df[f"{level}_ra"] - df[f"{level}_ex"]

# ===============================
# Chart 1 — Horizontal grouped bars
# ===============================
means = df.groupby("is_ft")[["simple_delta","moderate_delta","challenge_delta","overall_delta"]].mean()
others = means.loc[False].values  # Non‑FT
finetuned = means.loc[True].values

labels = ["Simple","Moderate","Challenge","Overall"]
y = np.arange(len(labels))
bar_h = 0.35

fig, ax = plt.subplots(figsize=(10,6))
b1 = ax.barh(y - bar_h/2, others, height=bar_h, label="Others")
b2 = ax.barh(y + bar_h/2, finetuned, height=bar_h, label="Fine‑tuned Methods")

# Value labels
for bars in (b1, b2):
    for rect in bars:
        w = rect.get_width()
        ax.annotate(f"{w:.1f}", (w, rect.get_y() + rect.get_height()/2),
                    xytext=(3,0), textcoords="offset points", va="center", fontsize=10)

ax.set_yticks(y)
ax.set_yticklabels(labels)
ax.set_xlabel("Mean RA − EX (pp)", fontsize=12)
ax.set_title("RA − EX Gap by Difficulty — Others vs Fine‑tuned", fontsize=16, pad=12)
ax.grid(axis="x", alpha=0.3)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Legend below the plot (avoid overlap with title)
ax.legend(frameon=False, ncols=2, loc="upper center", bbox_to_anchor=(0.5, -0.12))
plt.subplots_adjust(bottom=0.22)
plt.tight_layout()
plt.savefig("fig_bars_horizontal_others_vs_ft.png", bbox_inches="tight", dpi=200)
plt.close()

# ===============================
# Chart 2 — SOTA timeline (Others only), event‑spaced + smooth curve
# ===============================
sota_events = [
    ("2023-Jul", "C3-SQL", 3.9),
    ("2023-Nov", "DAIL-SQL", 6.8),
    ("2024-Jul", "SuperSQL", 7.5),
    ("2024-Sep", "Opensearch", 11.6),
    ("2024-Oct", "RSL-SQL", 15.0),
]
dates   = [e[0] for e in sota_events]
methods = [e[1] for e in sota_events]
y_vals  = np.array([e[2] for e in sota_events], dtype=float)

# Equally spaced events
x = np.arange(1, len(sota_events) + 1)

def gaussian_kernel_regression(x_obs, y_obs, x_eval, h):
    y_hat = np.zeros_like(x_eval, dtype=float)
    for i, xe in enumerate(x_eval):
        w = np.exp(-0.5 * ((xe - x_obs)/h)**2)
        y_hat[i] = np.sum(w * y_obs) / np.sum(w)
    return y_hat

x_smooth = np.linspace(x[0], x[-1], 400)
y_smooth = gaussian_kernel_regression(x, y_vals, x_smooth, h=0.9)

fig, ax = plt.subplots(figsize=(12,6))
ax.step(x, y_vals, where="post", linewidth=2.8, label="Running SOTA of (RA − EX)")
ax.plot(x_smooth, y_smooth, "-", linewidth=2.0, label="Smoothed trend")
ax.scatter(x, y_vals, s=55, label="Refresh event")

# Labels at points
for i, (xi, yi, name) in enumerate(zip(x, y_vals, methods)):
    ax.annotate(f"{yi:.1f}", (xi, yi), textcoords="offset points", xytext=(0,8),
                ha="center", fontsize=10)
    dy = 18 if i % 2 == 0 else -22
    ax.annotate(name, (xi, yi), textcoords="offset points", xytext=(0,dy),
                ha="center", fontsize=9)

ax.set_xticks(x)
ax.set_xticklabels(dates, rotation=15, ha="right")

ax.set_title("SOTA Progression of RA - EX - Others", fontsize=16, pad=12)
ax.set_xlabel("SOTA refresh events (equally spaced)", fontsize=12)
ax.set_ylabel("RA − EX (percentage points)", fontsize=12)
ax.grid(True, axis="y", alpha=0.3)
ax.legend(frameon=False)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("fig_sota_event_spaced_en.png", bbox_inches="tight", dpi=200)
plt.close()

print("Saved:", "fig_bars_horizontal_others_vs_ft.png", "fig_sota_event_spaced_en.png")
