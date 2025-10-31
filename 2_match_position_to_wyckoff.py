import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree
import glob
import os
import argparse
import sys
from pymatgen.symmetry.groups import SpaceGroup
import matplotlib.patches as mpatches
from scipy.signal import savgol_filter

# --- Argument parsing ---
parser = argparse.ArgumentParser(
    description="Plot free energy along Li trajectories with Wyckoff labels, and compute population/energy ratios."
)
parser.add_argument("csv_file", type=str, help="CSV file with fractional grid and free energy.")
parser.add_argument("xyz_dir", type=str, help="Directory with Li*_atom*.xyz files.")
parser.add_argument("--window", type=int, default=25, help="Smoothing window (default: 25)")
parser.add_argument("--tol", type=float, default=3e-2, help="Wyckoff matching tolerance (default: 0.03)")
parser.add_argument("--show-raw", action="store_true", help="Show raw energy points (scatter)")
parser.add_argument("--raw-only", action="store_true", help="Plot only raw energy points without smoothing curve")
parser.add_argument("--out-csv", type=str, default="site_ratios_vs_time.csv", help="Output CSV file for site ratios")
args = parser.parse_args()

# --- Load CSV energy grid ---
energy_df = pd.read_csv(args.csv_file)
grid_coords = energy_df[["x_frac", "y_frac", "z_frac"]].values
free_energies = energy_df["free_energy_eV"].values
tree = cKDTree(grid_coords)

# --- Generate Wyckoff reference positions ---
sg = SpaceGroup("Ia-3d")
def generate_positions(ref_pos):
    pos_list = [op.operate(ref_pos) % 1 for op in sg.symmetry_ops]
    return np.unique(np.round(pos_list, 6), axis=0)

positions_24d = generate_positions([0.375, 0, 0.25])
positions_96h = generate_positions([0.0959, 0.6922, 0.5731])
tree_24d = cKDTree(positions_24d)
tree_96h = cKDTree(positions_96h)

# --- Plot setup ---
plt.rcParams.update({
    'font.family': 'Liberation Serif',
    'font.size': 10,
})

plt.figure(figsize=(10, 5), dpi=300)
label_colors = {"24d": "blue", "96h": "green", "Other": "gray"}
tol = args.tol

# --- Prepare storage for time-resolved ratios ---
time_records = []

# --- Process each trajectory ---
xyz_files = sorted(glob.glob(os.path.join(args.xyz_dir, "Li10_frac_coords_atom*.xyz")))
if not xyz_files:
    sys.exit("No Li10_frac_coords_atom*.xyz files found in the specified directory.")

traj_len = None

for file in xyz_files:
    traj = []
    with open(file, "r") as f:
        for line in f:
            if line.startswith("#") or line.strip() == "":
                continue
            parts = line.strip().split()
            if len(parts) != 4:
                continue
            _, fx, fy, fz = parts
            traj.append([float(fx), float(fy), float(fz)])
    traj = np.array(traj)
    if traj_len is None:
        traj_len = traj.shape[0]

    # Map trajectory to energy grid
    _, idxs = tree.query(traj, k=1)
    raw_energies = free_energies[idxs]

    if not args.raw_only:
        smoothed = pd.Series(raw_energies).rolling(window=args.window, center=True, min_periods=1).mean().values

    # Wyckoff labeling
    labels = []
    for i, coord in enumerate(traj):
        d24, _ = tree_24d.query(coord)
        d96, _ = tree_96h.query(coord)
        if d24 < tol and d24 < d96:
            labels.append("24d")
        elif d96 < tol and d96 < d24:
            labels.append("96h")
        else:
            labels.append("Other")

    # Plot
    if not args.raw_only:
        plt.plot(smoothed, label=os.path.basename(file), linewidth=1)

    if args.show_raw or args.raw_only:
        for lbl, color in label_colors.items():
            idxs = [i for i, l in enumerate(labels) if l == lbl]
            plt.scatter(idxs, raw_energies[idxs], s=8, alpha=0.4, color=color)

    # --- Accumulate per-step site counts and energies ---
    for step in range(traj_len):
        site = labels[step]
        energy = raw_energies[step]
        if len(time_records) <= step:
            time_records.append({"step": step, "24d_count": 0, "96h_count": 0, "other_count": 0,
                                 "24d_energy": 0.0, "96h_energy": 0.0, "other_energy": 0.0})
        if site == "24d":
            time_records[step]["24d_count"] += 1
            time_records[step]["24d_energy"] += energy
        elif site == "96h":
            time_records[step]["96h_count"] += 1
            time_records[step]["96h_energy"] += energy
        else:
            time_records[step]["other_count"] += 1
            time_records[step]["other_energy"] += energy

# --- Convert to DataFrame ---
df_time = pd.DataFrame(time_records)

# Ratios and averages (all in 96h/24d convention)
df_time["pop_ratio_96h_24d"] = df_time.apply(
    lambda r: r["96h_count"]/r["24d_count"] if r["24d_count"] > 0 else np.nan, axis=1)
df_time["avg_E_24d"] = df_time.apply(
    lambda r: r["24d_energy"]/r["24d_count"] if r["24d_count"] > 0 else np.nan, axis=1)
df_time["avg_E_96h"] = df_time.apply(
    lambda r: r["96h_energy"]/r["96h_count"] if r["96h_count"] > 0 else np.nan, axis=1)
df_time["energy_ratio_96h_24d"] = df_time.apply(
    lambda r: r["avg_E_96h"]/r["avg_E_24d"]
    if pd.notnull(r["avg_E_96h"]) and pd.notnull(r["avg_E_24d"]) else np.nan, axis=1
)

# Overall averages
summary = {
    "mean_pop_ratio": df_time["pop_ratio_96h_24d"].mean(skipna=True),
    "mean_avg_E_24d": df_time["avg_E_24d"].mean(skipna=True),
    "mean_avg_E_96h": df_time["avg_E_96h"].mean(skipna=True),
    "mean_energy_ratio": df_time["energy_ratio_96h_24d"].mean(skipna=True),
}
print("[+] Overall averages (96h/24d convention):")
for k, v in summary.items():
    print(f"    {k} = {v:.4f}")

# Save CSV
df_time.to_csv(args.out_csv, index=False)
print(f"[+] Time-resolved site ratios saved to {args.out_csv}")

# --- Finalize free energy plot ---
patch_24d = mpatches.Patch(color='blue', label='24d sites')
patch_96h = mpatches.Patch(color='green', label='96h sites')
patch_other = mpatches.Patch(color='gray', label='Other sites')
legend_title = f"Wyckoff site match (tol = {tol:.3f})"
plt.legend(handles=[patch_24d, patch_96h, patch_other], title=legend_title, loc='lower right')

plt.xlabel("Time Step Index")
plt.ylabel("Free Energy (eV)")
plt.title("Free Energy Along All Lithium Ion Trajectories")
plt.grid(True, linestyle="--", alpha=0.3)
plt.tight_layout()
outname = "Li_all_trajectories_free_energy.png"
plt.savefig(outname)
print(f"[+] Plot saved as {outname}")
plt.show()

# --- Smoothed ratios plot ---
window_length = 51  # must be odd
polyorder = 3
pop_ratio_smoothed = savgol_filter(
    df_time["pop_ratio_96h_24d"].fillna(method="ffill").fillna(method="bfill"),
    window_length=window_length, polyorder=polyorder
)
energy_ratio_smoothed = savgol_filter(
    df_time["energy_ratio_96h_24d"].fillna(method="ffill").fillna(method="bfill"),
    window_length=window_length, polyorder=polyorder
)

plt.figure(figsize=(10, 5), dpi=300)
ax1 = plt.gca()
ax2 = ax1.twinx()

ax1.plot(df_time["step"], pop_ratio_smoothed,
         color="purple", lw=1.5, label="Population Ratio (96h/24d, smoothed)")
ax1.set_xlabel("Time Step Index")
ax1.set_ylabel("Population Ratio (96h/24d)", color="purple")
ax1.tick_params(axis='y', labelcolor="purple")

ax2.plot(df_time["step"], energy_ratio_smoothed,
         color="darkred", lw=1.5, linestyle="--", label="Energy Ratio (96h/24d, smoothed)")
ax2.set_ylabel("Energy Ratio (96h/24d)", color="darkred")
ax2.tick_params(axis='y', labelcolor="darkred")

plt.title("Per-step Li Site Population and Energy Ratios (96h/24d, Smoothed)")
ax1.grid(True, linestyle="--", alpha=0.3)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
plt.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

plt.tight_layout()
plt.savefig("Li_population_energy_ratios_smoothed.png")
print("[+] Plot saved as Li_population_energy_ratios_smoothed.png")
plt.show()

# --- Determine common range for ratios ---
pop_min, pop_max = np.nanmin(pop_ratio_smoothed), np.nanmax(pop_ratio_smoothed)
ener_min, ener_max = np.nanmin(energy_ratio_smoothed), np.nanmax(energy_ratio_smoothed)

common_min = min(pop_min, ener_min)
common_max = max(pop_max, ener_max)

# --- Rescale both series into the common range ---
def rescale(series, old_min, old_max, new_min, new_max):
    return (series - old_min) / (old_max - old_min) * (new_max - new_min) + new_min

pop_ratio_scaled = rescale(pop_ratio_smoothed, pop_min, pop_max, common_min, common_max)
energy_ratio_scaled = rescale(energy_ratio_smoothed, ener_min, ener_max, common_min, common_max)

# --- Plot scaled ratios on SAME y-axis ---
plt.figure(figsize=(10, 5), dpi=300)

plt.plot(df_time["step"], pop_ratio_scaled,
         color="purple", lw=1.5, label="Population Ratio (96h/24d, scaled)")
plt.plot(df_time["step"], energy_ratio_scaled,
         color="darkred", lw=1.5, linestyle="--", label="Energy Ratio (96h/24d, scaled)")

plt.xlabel("Time Step Index")
plt.ylabel("Scaled Ratios (common range)")
plt.title("Per-step Li Site Population and Energy Ratios (Scaled to Common Range)")
plt.grid(True, linestyle="--", alpha=0.3)
plt.legend(loc="upper right")

plt.tight_layout()
plt.savefig("Li_population_energy_ratios_scaled.png")
print("[+] Plot saved as Li_population_energy_ratios_scaled.png")
plt.show()


# --- Derivatives (original + smoothed) ---

# Clean up NaNs first
pop_orig = df_time["pop_ratio_96h_24d"].fillna(method="ffill").fillna(method="bfill").values
ener_orig = df_time["energy_ratio_96h_24d"].fillna(method="ffill").fillna(method="bfill").values

# Use uniform dt = 1 (since step index increments by 1)
dt = 1  

# Derivatives for original data
dpop_dt_orig = np.gradient(pop_orig, dt)
dener_dt_orig = np.gradient(ener_orig, dt)

# Derivatives for smoothed data
dpop_dt_smooth = np.gradient(pop_ratio_smoothed, dt)
dener_dt_smooth = np.gradient(energy_ratio_smoothed, dt)

# --- Plot derivatives ---

# Population ratio derivative
plt.figure(figsize=(10, 5), dpi=300)
plt.plot(df_time["step"], dpop_dt_orig, color="gray", lw=1, alpha=0.6, label="Original d(Pop)/dt")
plt.plot(df_time["step"], dpop_dt_smooth, color="purple", lw=1.5, label="Smoothed d(Pop)/dt")
plt.xlabel("Time Step Index")
plt.ylabel("d(Population Ratio)/dt")
plt.title("Derivative of Population Ratio (96h/24d)")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.3)
plt.tight_layout()
plt.savefig("Li_population_ratio_derivatives.png")
print("[+] Plot saved as Li_population_ratio_derivatives.png")
plt.show()

# Energy ratio derivative
plt.figure(figsize=(10, 5), dpi=300)
plt.plot(df_time["step"], dener_dt_orig, color="gray", lw=1, alpha=0.6, label="Original d(Energy)/dt")
plt.plot(df_time["step"], dener_dt_smooth, color="darkred", lw=1.5, label="Smoothed d(Energy)/dt")
plt.xlabel("Time Step Index")
plt.ylabel("d(Energy Ratio)/dt")
plt.title("Derivative of Energy Ratio (96h/24d)")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.3)
plt.tight_layout()
plt.savefig("Li_energy_ratio_derivatives.png")
print("[+] Plot saved as Li_energy_ratio_derivatives.png")
plt.show()


# --- Cross plots (Population vs Energy Ratios) ---

# Original cross plot
plt.figure(figsize=(6, 6), dpi=300)
plt.scatter(pop_orig, ener_orig, s=10, alpha=0.6, c=df_time["step"], cmap="viridis")
plt.xlabel("Population Ratio (96h/24d, original)")
plt.ylabel("Energy Ratio (96h/24d, original)")
plt.title("Population vs Energy Ratio (Original Data)")
cbar = plt.colorbar(label="Time Step Index")
plt.grid(True, linestyle="--", alpha=0.3)
plt.tight_layout()
plt.savefig("Li_population_vs_energy_ratio_original.png")
print("[+] Plot saved as Li_population_vs_energy_ratio_original.png")
plt.show()

# Smoothed cross plot
plt.figure(figsize=(6, 6), dpi=300)
plt.scatter(pop_ratio_smoothed, energy_ratio_smoothed, s=10, alpha=0.6, c=df_time["step"], cmap="plasma")
plt.xlabel("Population Ratio (96h/24d, smoothed)")
plt.ylabel("Energy Ratio (96h/24d, smoothed)")
plt.title("Population vs Energy Ratio (Smoothed Data)")
cbar = plt.colorbar(label="Time Step Index")
plt.grid(True, linestyle="--", alpha=0.3)
plt.tight_layout()
plt.savefig("Li_population_vs_energy_ratio_smoothed.png")
print("[+] Plot saved as Li_population_vs_energy_ratio_smoothed.png")
plt.show()

