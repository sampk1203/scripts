import MDAnalysis as mda
import matplotlib.pyplot as plt
import numpy as np
import statsmodels.api as sm
import argparse
import sys

def main():
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="Compute Radius of Gyration ($R_g$) and its Autocorrelation Function for polymer chains."
    )
    parser.add_argument("-d", "--data", required=True, help="Path to the LAMMPS data file (topology)")
    parser.add_argument("-trj", "--trajectory", required=True, help="Path to the trajectory file (dump)")
    parser.add_argument("-types", "--atom_types", nargs=3, required=True, 
                        help="The atom types for C, H, and O in order (e.g., 1 4 7)")
    parser.add_argument("-o", "--output", default="rg_equilibration.png", help="Output filename for the plot")

    # If no arguments are provided, print help and exit
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    # --- MDAnalysis Setup ---
    # Load the universe
    u = mda.Universe(args.data, args.trajectory, format="LAMMPSDUMP")

    # Construct the selection string from user input
    selection_string = f"type {' '.join(args.atom_types)}"
    peo = u.select_atoms(selection_string)

    # Identify individual chains
    chains = peo.fragments
    print(f"Found {len(chains)} polymer chains.")

    # --- Calculations ---
    all_rg = []
    times = []

    print("Processing trajectory (unwrapping and computing Rg)...")
    for ts in u.trajectory:
        # Mean Rg across all chains for the current frame
        current_frame_rgs = [c.radius_of_gyration(pbc=True) for c in chains]
        all_rg.append(np.mean(current_frame_rgs))
        times.append(ts.time)

    all_rg = np.array(all_rg)

    # --- Autocorrelation ---
    # Detrend the data
    rg_detrended = all_rg - np.mean(all_rg)
    acf = sm.tsa.acf(rg_detrended, nlags=len(all_rg)//2, fft=True)

    # --- Plotting ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 10))

    # Time series
    ax1.plot(times, all_rg, color='#2c3e50', lw=1.5)
    ax1.set_title("Polymer Radius of Gyration ($R_g$) Evolution")
    ax1.set_xlabel("Time (ps)")
    ax1.set_ylabel(r"$R_g$ ($\AA$)")
    ax1.grid(alpha=0.3)

    # Autocorrelation
    ax2.plot(acf, color='#e67e22', lw=2)
    ax2.axhline(0, color='black', linestyle='--')
    ax2.set_title("Normalized $R_g$ Autocorrelation Function")
    ax2.set_xlabel("Lag (Frames)")
    ax2.set_ylabel("ACF")
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(args.output, dpi=300)
    print(f"Plot saved to {args.output}")
    plt.show()

    print(f"Average Rg: {np.mean(all_rg):.3f} Å")

if __name__ == "__main__":
    main()