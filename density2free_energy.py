import numpy as np
import pandas as pd
import argparse
import os

# Constants
kB_ev_per_K = 8.617333262145e-5  # Boltzmann constant in eV/K
temperature = 300  # Temperature in Kelvin

def main():
    parser = argparse.ArgumentParser(description="Compute free energy from density in a CSV file.")
    parser.add_argument("input_csv", help="Input CSV file with columns: x_frac, y_frac, z_frac, density")
    args = parser.parse_args()

    input_path = os.path.abspath(args.input_csv)
    input_dir = os.path.dirname(input_path)
    output_csv = os.path.join(input_dir, "density_with_free_energy.csv")

    # Load CSV data
    data = pd.read_csv(input_path)

    # Check for non-positive densities
    if (data['density'] <= 0).any():
        raise ValueError("Density contains zero or negative values; cannot compute logarithm.")

    # Compute free energy: F(r) = -kB*T * ln(rho)
    data['free_energy_eV'] = -kB_ev_per_K * temperature * np.log(data['density'])

    # Normalize free energy to minimum = 0
    data['free_energy_eV'] -= data['free_energy_eV'].min()

    # Save result
    data.to_csv(output_csv, index=False)
    print(f"✅ Free energy computed and saved to '{output_csv}'")

if __name__ == "__main__":
    main()

