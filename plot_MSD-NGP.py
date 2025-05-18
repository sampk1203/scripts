import argparse
import matplotlib.pyplot as plt
import os
import sys

def plot_msd_ngp(file_path):
    if not os.path.isfile(file_path):
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)

    time = []
    msd = []
    ngp = []

    with open(file_path, 'r') as f:
        lines = f.readlines()[1:]  # Skip the first line

    for line in lines:
        if line.strip() == "":
            continue
        values = line.strip().split()
        if len(values) < 3:
            continue
        t, m, n = map(float, values[:3])
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
    parser.add_argument('file', type=str, help='Path to input text file (tab completion works in shell).')
    args = parser.parse_args()

    plot_msd_ngp(args.file)

