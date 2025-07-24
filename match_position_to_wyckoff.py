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
# --- Argument parsing ---
parser = argparse.ArgumentParser(
    description="Plot free energy along Li trajectories with Wyckoff labels."
)
parser.add_argument("csv_file", type=str, help="CSV file with fractional grid and free energy.")
parser.add_argument("xyz_dir", type=str, help="Directory with Li*_atom*.xyz files.")
parser.add_argument("--window", type=int, default=25, help="Smoothing window (default: 25)")
parser.add_argument("--tol", type=float, default=3e-2, help="Wyckoff matching tolerance (default: 0.05)")
parser.add_argument("--show-raw", action="store_true", help="Show raw energy points (scatter)")
parser.add_argument("--raw-only", action="store_true", help="Plot only raw energy points without smoothing curve")
args = parser.parse_args()

# --- Load CSV energy grid ---
energy_df = pd.read_csv(args.csv_file)
grid_coords = energy_df[["x_frac", "y_frac", "z_frac"]].values
free_energies = energy_df["free_energy_eV"].values
tree = cKDTree(grid_coords)

# --- Generate Wyckoff reference ---
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

total_24d = 0
total_96h = 0
energy_sum_24d = 0.0
energy_sum_96h = 0.0

# --- Process each trajectory ---
xyz_files = sorted(glob.glob(os.path.join(args.xyz_dir, "Li10_frac_coords_atom*.xyz")))
if not xyz_files:
    sys.exit("No Li10_frac_coords_atom*.xyz files found in the specified directory.")

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

    # Map to energy grid
    _, idxs = tree.query(traj, k=1)
    raw_energies = free_energies[idxs]

    if not args.raw_only:
        smoothed = pd.Series(raw_energies).rolling(window=args.window, center=True, min_periods=1).mean().values

    # Wyckoff labeling
    labels = []
    for i, coord in enumerate(traj):
        d24, _ = tree_24d.query(coord)
        d96, _ = tree_96h.query(coord)
        energy = raw_energies[i]
        if d24 < tol and d24 < d96:
            labels.append("24d")
            total_24d += 1
            energy_sum_24d += energy
        elif d96 < tol and d96 < d24:
            labels.append("96h")
            total_96h += 1
            energy_sum_96h += energy
        else:
            labels.append("Other")

    label_indices = {"24d": [], "96h": [], "Other": []}
    for i, lbl in enumerate(labels):
        label_indices[lbl].append(i)

    # Plot
    if not args.raw_only:
        plt.plot(smoothed, label=os.path.basename(file), linewidth=1)

    if args.show_raw or args.raw_only:
        for lbl in label_indices:
            idxs = label_indices[lbl]
            plt.scatter(idxs, raw_energies[idxs], s=8, alpha=0.4, color=label_colors[lbl])

# --- After plotting all trajectories and before finalizing plot ---

# Create legend handles for site types with colors and tolerance info
patch_24d = mpatches.Patch(color='blue', label='24d sites')
patch_96h = mpatches.Patch(color='green', label='96h sites')
patch_other = mpatches.Patch(color='gray', label='Other sites')

legend_title = f"Wyckoff site match (tol = {tol:.3f})"
plt.legend(handles=[patch_24d, patch_96h, patch_other], title=legend_title, loc='lower right')

# --- Finalize plot ---
plt.xlabel("Time Step Index")
plt.ylabel("Free Energy (eV)")
plt.title("Free Energy Along All Lithium Ion Trajectories")
plt.grid(True, linestyle="--", alpha=0.3)
plt.tight_layout()

outname = "Li_all_trajectories_free_energy.png"
plt.savefig(outname)
print(f"[+] Plot saved as {outname}")
plt.show()

# --- Print population and energy ratios ---
if total_24d > 0 and total_96h > 0:
    pop_ratio = total_96h / total_24d
    avg_E_24d = energy_sum_24d / total_24d
    avg_E_96h = energy_sum_96h / total_96h
    energy_ratio = avg_E_24d / avg_E_96h
    print(f"[+] 96h/24d population ratio = {pop_ratio:.3f} ({total_96h}/{total_24d})")
    print(f"[+] Avg energy (24d) = {avg_E_24d:.4f} eV")
    print(f"[+] Avg energy (96h) = {avg_E_96h:.4f} eV")
    print(f"[+] Energy ratio (24d/96h) = {energy_ratio:.3f}")
else:
    print("[-] One of the site types has zero count — cannot compute ratios.")

