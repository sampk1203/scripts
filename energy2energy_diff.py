import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
import argparse
import os

def local_interpolation(coord, tree, points, values, k=4):
    dists, idxs = tree.query(coord, k=k)
    if k == 1:
        return values[idxs]
    weights = 1 / (dists + 1e-12)
    weights /= weights.sum()
    interpolated_value = np.dot(weights, values[idxs])
    return interpolated_value

def free_energy_difference(coord1, coord2, tree, points, values, k=4):
    F1 = local_interpolation(coord1, tree, points, values, k)
    F2 = local_interpolation(coord2, tree, points, values, k)
    delta_F = round(float(F2 - F1), 6)
    F1 = round(float(F1), 6)
    F2 = round(float(F2), 6)
    return delta_F, F1, F2

def parse_fractional_coords(arg):
    parts = arg.strip().split(',')
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("Fractional coordinates must be in 'x,y,z' format.")
    return [float(x) for x in parts]

def main():
    parser = argparse.ArgumentParser(description="Compute free energy difference between two fractional coordinates.")
    parser.add_argument("input_csv", help="Path to input CSV file with 'density_with_free_energy.csv' structure")
    parser.add_argument("-n1", "--node1", type=parse_fractional_coords, required=True, help="First fractional coordinate (e.g., 0.1,0.2,0.3)")
    parser.add_argument("-n2", "--node2", type=parse_fractional_coords, required=True, help="Second fractional coordinate (e.g., 0.4,0.5,0.6)")
    parser.add_argument("-k", type=int, default=4, help="Number of neighbors to use for interpolation (default: 4)")
    args = parser.parse_args()

    # Load data
    data = pd.read_csv(args.input_csv)
    points = data[['x_frac', 'y_frac', 'z_frac']].values
    values = data['free_energy_eV'].values
    tree = cKDTree(points)

    delta_F, F1, F2 = free_energy_difference(args.node1, args.node2, tree, points, values, k=args.k)

    print(f"Interpolated free energy at {args.node1}: {F1} eV")
    print(f"Interpolated free energy at {args.node2}: {F2} eV")
    print(f"Free energy difference ΔF = F2 - F1 = {delta_F} eV")

if __name__ == "__main__":
    main()

