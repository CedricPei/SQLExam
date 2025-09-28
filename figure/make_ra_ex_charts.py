import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
data = [
    ("OpenSearch-SQL", "Sep 2024", "DeepSeek-Chat", 77.94, 91.18, 69.78, 80.44, 56.25, 67.71, 69.37, 80.96),
    ("CSC-SQL-32B", "May 2025", "FT", 85.00, 87.14, 71.99, 77.54, 53.06, 67.35, 71.52, 78.27),
    ("Alpha-SQL-32B", "Feb 2025", "Qwen2.5 Coder 32B", 81.02, 91.24, 69.47, 79.65, 52.58, 70.10, 69.35, 81.09),
    ("RSL-SQL", "Oct 2024", "GPT-4o", 80.15, 91.18, 64.60, 80.09, 53.61, 73.20, 66.88, 81.92),
    ("RSL-SQL", "Oct 2024", "DeepSeek-Chat", 74.29, 86.43, 59.83, 71.79, 52.04, 62.24, 62.50, 74.15),
    ("SuperSQL", "Jul 2024", "GPT-4", 67.65, 72.79, 48.66, 69.38, 45.83, 48.96, 53.73, 61.18),
    ("CodeS-15B", "Feb 2024", "FT", 64.96, 67.15, 46.90, 44.69, 39.13, 32.61, 50.77, 49.01),
    ("OmniSQL-32B", "Mar 2025", "FT", 80.00, 86.43, 67.23, 78.30, 57.14, 72.45, 68.92, 79.49),
    ("DAIL-SQL", "Nov 2023", "GPT-4", 62.50, 72.06, 44.64, 52.68, 38.95, 38.95, 48.79, 55.60),
    ("TA-SQL", "May 2024", "GPT-4o", 66.67, 71.74, 49.05, 54.66, 33.67, 44.90, 51.06, 57.63),
    ("CHESS-V1", "May 2024", "FT", 70.50, 70.50, 58.20, 62.87, 45.92, 48.98, 59.28, 62.24),
    ("CoT", "Mar 2023", "GPT-3.5", 42.65, 50.00, 21.05, 28.07, 13.54, 19.79, 25.87, 32.83),
    ("C3-SQL", "Jul 2023", "GPT-3.5", 61.03, 62.50, 36.89, 43.11, 28.87, 30.93, 42.36, 46.29),
    ("RESD SQL-3B", "Feb 2023", "FT", 56.30, 54.07, 31.44, 31.00, 17.71, 15.62, 35.87, 34.57),
]
cols = ["method","date_str","model","simple_ex","simple_prose","moderate_ex","moderate_prose",
        "challenge_ex","challenge_prose","overall_ex","overall_prose"]
df = pd.DataFrame(data, columns=cols)

base_models = [
    ("GPT-5",       "Aug 2025", "Base", np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, 55.74, 88.93),
    ("DeepSeek-Chat", "Mar 2025", "Base", np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, 52.13, 72.21),
    ("GPT-4o",      "May 2025", "Base", np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, 52.20, 71.37),
    ("GPT-4",       "Apr 2024", "Base", np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, 48.98, 66.53),
    ("GPT-3.5",     "Jan 2024", "Base", np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, 41.22, 50.61),
]
df = pd.concat([df, pd.DataFrame(base_models, columns=cols)], ignore_index=True)

def parse_dt(s):
    try:
        return pd.to_datetime(s)
    except Exception:
        return pd.to_datetime(s, format="%b %Y")

df["date"] = df["date_str"].apply(parse_dt)
df["is_ft"] = df["model"] == "FT"
df["is_base"] = df["model"] == "Base"
for level in ["simple","moderate","challenge","overall"]:
    df[f"{level}_delta"] = df[f"{level}_prose"].astype(float) - df[f"{level}_ex"].astype(float)

os.makedirs("figure", exist_ok=True)
means = df.groupby("is_ft")[["overall_delta","challenge_delta","moderate_delta","simple_delta"]].mean()
others = means.loc[False].values
finetuned = means.loc[True].values

labels = ["Overall","Challenge","Moderate","Simple"]
y = np.arange(len(labels))
bar_h = 0.35

fig, ax = plt.subplots(figsize=(10,6))
b1 = ax.barh(y - bar_h/2, others, height=bar_h, label="Prompting")
b2 = ax.barh(y + bar_h/2, finetuned, height=bar_h, label="Fine-tuned")

for bars in (b1, b2):
    for rect in bars:
        w = rect.get_width()
        ax.annotate(f"{w:.1f}", (w, rect.get_y() + rect.get_height()/2),
                    xytext=(3,0), textcoords="offset points", va="center", fontsize=14)

ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=16)
ax.set_xlabel("Mean PROSE - EX", fontsize=16)
plt.setp(ax.get_xticklabels(), fontsize=12)
ax.grid(axis="x", alpha=0.3)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.12), fontsize=16)
plt.subplots_adjust(bottom=0.22)
plt.tight_layout()
plt.savefig("figure/diff_method.png", bbox_inches="tight", dpi=200)
plt.close()

# Convert PNG to PDF using Pillow
from PIL import Image
img = Image.open("figure/diff_method.png")
# Convert RGBA to RGB if necessary
if img.mode == 'RGBA':
    img = img.convert('RGB')
img.save("figure/diff_method.pdf", "PDF")



system_df = df[(~df["is_ft"]) & (~df["is_base"])].copy().sort_values("date")
system_df = system_df[system_df["overall_delta"].notna()]
base_df   = df[df["is_base"]].copy().sort_values("date")
base_df   = base_df[base_df["overall_delta"].notna()]

all_pts = pd.concat(
    [system_df[["date","overall_delta","method","model"]],
     base_df[["date","overall_delta","method","model"]]],
    ignore_index=True
).sort_values("date")

def _fit_logistic_given_AK(x_norm, y, A, K):
    eps = 1e-9
    s = (K - A) / (y - A + eps) - 1.0
    s = np.clip(s, 1e-6, 1e6)
    z = np.log(s)
    p = np.polyfit(x_norm, z, 1)
    k  = -p[0]
    t0 = p[1] / (k + 1e-12)
    return k, t0

def fit_logistic_monotone_raw(x_raw, y):
    x_min, x_max = float(x_raw.min()), float(x_raw.max())
    span  = max(x_max - x_min, 1e-12)
    x_norm = (x_raw - x_min) / span
    y = y.astype(float)
    yr = y.max() - y.min()
    A0, K0 = y.min() - 0.10*yr, y.max() + 0.10*yr
    best = None
    for A in np.linspace(A0 - 0.25*yr, A0 + 0.25*yr, 21):
        for K in np.linspace(K0 - 0.25*yr, K0 + 0.25*yr, 21):
            if K <= A + 1e-6: 
                continue
            k, t0 = _fit_logistic_given_AK(x_norm, y, A, K)
            if not np.isfinite(k) or not np.isfinite(t0) or k <= 0:
                continue
            yhat = A + (K - A) / (1 + np.exp(-k*(x_norm - t0)))
            sse  = np.mean((y - yhat)**2)
            if best is None or sse < best[0]:
                best = (sse, (A, K, k, t0))
    if best is None:
        p = np.polyfit(x_norm, y, 1)
        return (p[1], p[1]+p[0], max(p[0],1e-6), 0.5), (x_min, x_max)
    return best[1], (x_min, x_max)

def logistic_predict_raw(x_eval_raw, x_min, x_max, params):
    A, K, k, t0 = params
    span  = max(x_max - x_min, 1e-12)
    x_norm = (x_eval_raw - x_min) / span
    return A + (K - A) / (1 + np.exp(-k*(x_norm - t0)))

x_raw_all = mdates.date2num(all_pts["date"].to_list()).astype(float)
y_all     = all_pts["overall_delta"].to_numpy(dtype=float)
params, (xmin_raw, xmax_raw) = fit_logistic_monotone_raw(x_raw_all, y_all)
x_eval_raw = np.linspace(x_raw_all.min(), x_raw_all.max(), 600)
y_eval     = logistic_predict_raw(x_eval_raw, xmin_raw, xmax_raw, params)

fig, ax = plt.subplots(figsize=(10,6))

pad_days = pd.Timedelta(days=120)
ax.set_xlim(all_pts["date"].min() - pad_days, all_pts["date"].max() + pad_days)

all_vals = pd.concat([system_df["overall_delta"], base_df["overall_delta"], pd.Series(y_eval)])
span = all_vals.max() - all_vals.min()
ax.set_ylim(all_vals.min() - max(0.06*span, 0.5), all_vals.max() + max(0.06*span, 0.5))

ax.scatter(system_df["date"], system_df["overall_delta"], s=70, label="System")
ax.scatter(base_df["date"],    base_df["overall_delta"],    s=90, marker="D", label="Base Model")

x_eval_dates = mdates.num2date(x_eval_raw)
ax.plot(x_eval_dates, y_eval, linestyle="--", linewidth=2.0, color="red", label="Logistic Trend")

def _abbr_for_rsl(model_str: str) -> str:
    ms = str(model_str).lower()
    if "deepseek" in ms: return "DS"
    if "gpt" in ms:      return "GPT"
    return ""

def _point_label(method, model):
    if method == "RSL-SQL":
        abbr = _abbr_for_rsl(model)
        return f"RSL-SQL ({abbr})" if abbr else "RSL-SQL"
    else:
        return str(method)



for _, r in system_df.iterrows():
    txt = _point_label(r["method"], r["model"])
    if r["method"] == "OpenSearch-SQL":
        ax.annotate(txt, (r["date"], r["overall_delta"]),
                    textcoords="offset points", xytext=(5, -7),
                    ha="right", va="top", fontsize=12)
    elif r["method"] == "DeepSeek-Chat":
        ax.annotate(txt, (r["date"], r["overall_delta"]),
                    textcoords="offset points", xytext=(-30, 15),
                    ha="right", va="bottom", fontsize=12,
                    bbox=dict(fc="white", ec="none", alpha=0.85, pad=0.2))
    elif r["method"] == "Alpha-SQL-32B":
        ax.annotate(txt, (r["date"], r["overall_delta"]),
                    textcoords="offset points", xytext=(10, 0),
                    ha="left", va="center", fontsize=12)
    elif r["method"] == "SuperSQL":
        ax.annotate(txt, (r["date"], r["overall_delta"]),
                    textcoords="offset points", xytext=(6, -5),
                    ha="left", va="top", fontsize=12)
    elif r["method"] == "RSL-SQL":
        ax.annotate(txt, (r["date"], r["overall_delta"]),
                    textcoords="offset points", xytext=(-5, -7),
                    ha="left", va="top", fontsize=12)
    else:
        ax.annotate(txt, (r["date"], r["overall_delta"]),
                    textcoords="offset points", xytext=(0, -8),
                    ha="center", va="top", fontsize=12)

for _, r in base_df.iterrows():
    txt = _point_label(r["method"], r["model"])
    if r["method"] == "DeepSeek-Chat":
        ax.annotate(txt, (r["date"], r["overall_delta"]),
                    textcoords="offset points", xytext=(0, 8),
                    ha="center", va="bottom", fontsize=12)
    else:
        ax.annotate(txt, (r["date"], r["overall_delta"]),
                    textcoords="offset points", xytext=(0, -8),
                    ha="center", va="top", fontsize=12)

ax.set_xlabel("Date", fontsize=16)
ax.set_ylabel("PROSE − EX", fontsize=16)
ax.grid(True, axis="y", alpha=0.3)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(frameon=False, ncol=3, loc="upper left", fontsize=14)
ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=6, maxticks=9))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%b"))
plt.setp(ax.get_xticklabels(), rotation=0, ha="center", fontsize=14)
plt.setp(ax.get_yticklabels(), fontsize=14)

plt.tight_layout()
plt.savefig("figure/diff_time.png", dpi=200, bbox_inches="tight")
plt.close()

# Convert PNG to PDF using Pillow
img2 = Image.open("figure/diff_time.png")
# Convert RGBA to RGB if necessary
if img2.mode == 'RGBA':
    img2 = img2.convert('RGB')
img2.save("figure/diff_time.pdf", "PDF")