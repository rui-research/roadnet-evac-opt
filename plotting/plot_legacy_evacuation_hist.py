import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common_paths import GENERATED_FIGURES, LEGACY

# 项目根目录（python/ 的上一级）。
PROJECT_ROOT = str(LEGACY)

def plot_and_analyze(csv_path,
                     state_done=0,
                     dist_thresh=300.0,
                     time_thresh=400.0,
                     bins_time=40,
                     bins_dist=40,
                     out_png=None):
    # --- Load ---
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]

    # --- Clean + filter completed ---
    df["state"] = pd.to_numeric(df["state"], errors="coerce")
    df["time"] = pd.to_numeric(df["time"], errors="coerce")
    df["distance"] = pd.to_numeric(df["distance"], errors="coerce")

    done = df[df["state"] == state_done].dropna(subset=["time", "distance"]).copy()
    done = done[(done["time"] >= 0) & (done["distance"] >= 0)]

    n = len(done)
    if n == 0:
        raise ValueError(f"No valid completed rows found (state={state_done}).")

    # --- Ratios ---
    p_dist = (done["distance"] <= dist_thresh).mean()
    p_time = (done["time"] <= time_thresh).mean()
    p_both = ((done["distance"] <= dist_thresh) & (done["time"] <= time_thresh)).mean()

    print(f"Completed samples (state={state_done}): {n}")
    print(f"Share with distance <= {dist_thresh:.0f} m: {p_dist*100:.2f}%")
    print(f"Share with time <= {time_thresh:.0f} s: {p_time*100:.2f}%")
    print(f"Share with BOTH (distance <= {dist_thresh:.0f} m AND time <= {time_thresh:.0f} s): {p_both*100:.2f}%")

    # --- Plot ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8))

    # Time histogram
    ax1.hist(done["time"].to_numpy(), bins=bins_time)
    # ax1.axvline(time_thresh, linewidth=2, color="k")
    ax1.set_title("Evacuation Time Histogram (Completed)")
    ax1.set_xlabel("Evacuation Time (s)")
    ax1.set_ylabel("Number of People")
    ax1.grid(True, alpha=0.25)

    # Distance histogram
    ax2.hist(done["distance"].to_numpy(), bins=bins_dist)
    # ax2.axvline(dist_thresh, linewidth=2, color="k")
    ax2.set_title("Evacuation Distance Histogram (Completed)")
    ax2.set_xlabel("Evacuation Distance (m)")
    ax2.set_ylabel("Number of People")
    ax2.grid(True, alpha=0.25)

    plt.tight_layout()

    if out_png:
        os.makedirs(os.path.dirname(out_png) or ".", exist_ok=True)
        plt.savefig(out_png, dpi=300, bbox_inches="tight")
        print("Saved:", out_png)

    plt.close(fig)

# Example:
plot_and_analyze(str(LEGACY / "baseline_run_record.csv"),
                 state_done=0,
                 dist_thresh=300,
                 time_thresh=400,
                 bins_time=50,
                 bins_dist=50,
                 out_png=str(GENERATED_FIGURES / "hist_time_distance.png"))
