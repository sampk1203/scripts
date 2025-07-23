import numpy as np
import matplotlib.pyplot as plt
import sys

# Check command-line input
if len(sys.argv) < 2:
    print("Usage: python plot_2col.py <datafile1> <datafile2> ...")
    sys.exit(1)

# Create the plot figure before plotting anything
plt.figure(figsize=(8, 5))

# Loop through all input files
for filename in sys.argv[1:]:
    data = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or line.startswith('@') or line == '':
                    continue
                parts = line.replace(',', ' ').split()
                if len(parts) >= 2:
                    try:
                        x, y = float(parts[0]), float(parts[1])
                        data.append([x, y])
                    except ValueError:
                        continue
        data = np.array(data)
        if data.shape[0] == 0:
            print(f"Warning: No valid data found in {filename}. Skipping.")
            continue

        # Plot the data
        plt.plot(data[:, 0], data[:, 1], label=filename)

    except FileNotFoundError:
        print(f"Error: File {filename} not found. Skipping.")
    except Exception as e:
        print(f"Error reading {filename}: {e}. Skipping.")

# Finalize plot
plt.xlabel("X")
plt.ylabel("Y")
plt.title("2-Column Plot")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

