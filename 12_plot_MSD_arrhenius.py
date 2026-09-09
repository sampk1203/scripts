import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
import os

# ==============================
# Helper Functions
# ==============================

def read_file(filename):
    """Read 2nd and 3rd columns from a txt or csv file."""
    try:
        data = np.loadtxt(filename, delimiter=",", skiprows=1)
    except ValueError:
        data = np.loadtxt(filename, skiprows=1)
    return data[:, 1], data[:, 2]  # 2nd and 3rd columns


def choose_plot_modes():
    print("Select plot modes (you can choose multiple, separated by commas):")
    print("1 - Linear")
    print("2 - Log-Log")
    print("3 - Semi-Log (Y log)")
    choices = input("Enter choices (e.g., 1,3): ").split(",")
    return [int(c.strip()) for c in choices if c.strip().isdigit()]


def linear_fit(x, y, x_start, x_end):
    mask = (x >= x_start) & (x <= x_end)
    x_fit = x[mask]
    y_fit = y[mask]

    if len(x_fit) < 2:
        raise ValueError("Not enough points in selected range for fitting.")

    slope, intercept, r_value, p_value, std_err = linregress(x_fit, y_fit)
    return slope, intercept, x_fit, slope * x_fit + intercept


def plot_all_final(all_data, fit_curves, plot_modes):
    """Plot all raw data and fits together in one figure."""
    n = len(plot_modes)
    plt.figure(figsize=(6 * n, 5))
    colors = plt.cm.tab10.colors  # up to 10 distinct colors

    for i, mode in enumerate(plot_modes, start=1):
        plt.subplot(1, n, i)
        for idx, (filename, (x, y)) in enumerate(all_data.items()):
            color = colors[idx % len(colors)]
            if mode == 1:
                plt.plot(x, y, color=color, label=os.path.basename(filename))
            elif mode == 2:
                plt.loglog(x, y, color=color, label=os.path.basename(filename))
            elif mode == 3:
                plt.semilogy(x, y, color=color, label=os.path.basename(filename))
        # Plot fit curves in same color but light transparent
        for idx, (filename, (x_fit, y_fit)) in enumerate(fit_curves.items()):
            color = colors[idx % len(colors)]
            plt.plot(x_fit, y_fit, "--", color=color, alpha=0.4)
        plt.xlabel("Column 2 (X)")
        plt.ylabel("Column 3 (Y)")
        plt.title({1: "Linear", 2: "Log-Log", 3: "Semi-Log (Y)"}[mode])
        plt.grid(True, which="both")
        plt.legend()

    plt.tight_layout()
    plt.show()


def arrhenius_fit(temps, diffusivities):
    temps = np.array(temps)
    diffusivities = np.array(diffusivities)

    x_arr = 1000.0 / temps
    y_arr = np.log(diffusivities)

    slope, intercept, r_value, p_value, std_err = linregress(x_arr, y_arr)
    y_fit = slope * x_arr + intercept

    plt.figure(figsize=(6, 4))
    plt.scatter(x_arr, y_arr, label="Data")
    plt.plot(x_arr, y_fit, "r--", label=f"Fit: y={slope:.4f}x+{intercept:.4f}")
    plt.xlabel("1000 / T (1/K)")
    plt.ylabel("ln(D)")
    plt.title("Arrhenius Fit")
    plt.legend()
    plt.grid(True)
    plt.show()

    D0 = np.exp(intercept)
    Ea = -slope * 8.615 * 0.01  # eV
    return slope, intercept, D0, Ea


# ==============================
# Main Execution
# ==============================

def main():
    if len(sys.argv) < 2:
        print("Usage: python multi_fit.py file1.txt file2.csv ...")
        sys.exit(1)

    filenames = sys.argv[1:]
    plot_modes = choose_plot_modes()

    # Global fitting range
    try:
        x_start = float(input("Enter start of x-range for fitting (linear): "))
        x_end = float(input("Enter end of x-range for fitting (linear): "))
    except ValueError:
        print("Invalid numeric input for range.")
        sys.exit(1)

    temps = []
    diffusivities = []
    all_data = {}
    fit_curves = {}

    for filename in filenames:
        x, y = read_file(filename)
        all_data[filename] = (x, y)

        try:
            temp = float(input(f"Enter temperature (K) for {filename}: "))
        except ValueError:
            print("Invalid temperature.")
            sys.exit(1)

        slope, intercept, x_fit, y_fit = linear_fit(x, y, x_start, x_end)
        fit_curves[filename] = (x_fit, y_fit)
        Diff = slope / 60000.0  # D in cm^2/s
        print(f"\nFile: {filename}")
        print(f"Slope: {slope:.6f}")
        print(f"Intercept: {intercept:.6f}")
        print(f"Diffusivity: {Diff:.3e} cm^2/s\n")

        temps.append(temp)
        diffusivities.append(Diff)

    # Final plot: all data + fit curves together
    plot_all_final(all_data, fit_curves, plot_modes)

    # Arrhenius fit
    slope_arr, intercept_arr, D0, Ea = arrhenius_fit(temps, diffusivities)
    print("====================")
    print("Arrhenius Fit Results")
    print(f"Slope: {slope_arr:.6f}")
    print(f"Intercept: {intercept_arr:.6f}")
    print(f"D0: {D0:.3e} cm^2/s")
    print(f"Ea: {Ea:.4f} eV")
    print("====================")

    # ===========================
    # Conductivity Calculation (New)
    # ===========================
    print("\n=== Conductivity Calculation ===")
    try:
        n_supercells = float(input("Enter number of supercells [default=1]: ") or 1)
        n_dopants = float(input("Enter number of dopants [default=0]: ") or 0)
        li_change = float(input("Enter Li added/removed per dopant (+ for added, - for removed) [default=0]: ") or 0)
    except ValueError:
        print("Invalid input. Using defaults.")
        n_supercells, n_dopants, li_change = 1, 0, 0

    # Constants
    volume_single = 2188.2405e-30  # m^3
    li_per_supercell = 46

    # Derived quantities
    n_Li_total = li_per_supercell * n_supercells + n_dopants * li_change
    volume_total = volume_single * n_supercells
    n_density = n_Li_total / volume_total  # m^-3

    print(f"\nTotal Li atoms: {n_Li_total:.3f}")
    print(f"Total Volume: {volume_total:.3e} m^3")
    print(f"Number Density (n): {n_density:.3e} m^-3")

    # Conductivity at 300K
    kB = 8.617333262145e-5  # eV/K
    T_ref = 300  # K
    D_300 = D0 * np.exp(-Ea / kB / T_ref)  # cm^2/s

    sigma = 6.25043e-22 * D_300 * n_density  # S/cm
    print("\n====================")
    print(f"At T = {T_ref} K:")
    print(f"Diffusivity D = {D_300:.3e} cm^2/s")
    print(f"Conductivity σ = {sigma:.3e} S/m")
    print("====================")


if __name__ == "__main__":
    main()
