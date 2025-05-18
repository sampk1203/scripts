import numpy as np
import csv
import argparse
import os

def parse_dx(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()

    origin = None
    deltas = []
    grid_size = []
    data = []
    reading_data = False

    for line in lines:
        if line.startswith("origin"):
            origin = np.array([float(x) for x in line.split()[1:]])
        elif line.startswith("delta"):
            deltas.append(float(line.split()[1]))
        elif line.startswith("object 1 class gridpositions counts"):
            grid_size = [int(x) for x in line.split()[5:]]
        elif line.startswith("object 3 class array type double"):
            reading_data = True
        elif reading_data:
            tokens = line.split()
            try:
                floats = [float(x) for x in tokens]
                data.extend(floats)
            except ValueError:
                break

    data = np.array(data).reshape(grid_size[::-1])  # z, y, x
    return data, origin, deltas, grid_size

def main():
    parser = argparse.ArgumentParser(description="Parse a .dx voxel file and write fractional coordinates + densities to CSV.")
    parser.add_argument("input_dx", help="Input .dx file path")
    args = parser.parse_args()

    input_path = os.path.abspath(args.input_dx)
    input_dir = os.path.dirname(input_path)
    output_csv = os.path.join(input_dir, "density_fractional.csv")

    # Parse DX file
    data, origin, deltas, grid_size = parse_dx(input_path)

    # Generate fractional coordinates
    nz, ny, nx = data.shape
    x = np.linspace(0, 1, nx)
    y = np.linspace(0, 1, ny)
    z = np.linspace(0, 1, nz)

    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    X = X.flatten()
    Y = Y.flatten()
    Z = Z.flatten()
    D = data.flatten()

    # Mask near-zero densities
    mask = D > 1e-6
    X, Y, Z, D = X[mask], Y[mask], Z[mask], D[mask]

    # Write CSV
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["x_frac", "y_frac", "z_frac", "density"])
        for x, y, z, d in zip(X, Y, Z, D):
            writer.writerow([x, y, z, d])

    print(f"✅ Done. Data written to '{output_csv}'")

if __name__ == "__main__":
    main()

