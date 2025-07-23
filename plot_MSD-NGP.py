import argparse
import matplotlib.pyplot as plt
import os
import sys

def plot_msd_ngp(file_path):
    if not os.path.isfile(file_path):
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)

    # Detect columns by scanning first non-comment, non-empty line
    header_line = None
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line == "" or line.startswith("#"):
                continue
            header_line = line
            break

    if header_line is None:
        print("Error: No valid data lines found (all lines are comments or empty).")
        sys.exit(1)

    sample_values = header_line.split()
    num_cols = len(sample_values)
    print(f"Detected {num_cols} columns in file.")
    print("Columns (1-based indices):")
    for idx, val in enumerate(sample_values, start=1):
        print(f"{idx}: sample={val}")

    # Ask user which columns to use
    time_col = int(input("Enter column number for TIME: ")) - 1
    msd_col  = int(input("Enter column number for MSD: ")) - 1
    ngp_col  = int(input("Enter column number for NGP: ")) - 1

    time = []
    msd = []
    ngp = []

    # Parse file, ignoring comment lines and incomplete rows
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line == "" or line.startswith("#"):
                continue
            values = line.split()
            if len(values) <= max(time_col, msd_col, ngp_col):
                continue
            try:
                t = float(values[time_col])
                m = float(values[msd_col])
                n = float(values[ngp_col])
            except ValueError:
                continue
            time.append(t)
            msd.append(m)
            ngp.append(n)

    # Plot MSD
    plt.figure(figsize=(8, 5))
    plt.plot(time, msd, label='MSD', color='blue')
    plt.xlabel('Time')
    plt.ylabel('Mean Squared Displacement (MSD)')
    plt.title('MSD vs Time')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # Plot NGP
    plt.figure(figsize=(8, 5))
    plt.plot(time, ngp, label='NGP', color='red')
    plt.xlabel('Time')
    plt.ylabel('Non-Gaussian Parameter (NGP)')
    plt.title('NGP vs Time')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plot MSD and NGP from a text file.')
    parser.add_argument('file', type=str, help='Path to input text file.')
    args = parser.parse_args()

    plot_msd_ngp(args.file)

