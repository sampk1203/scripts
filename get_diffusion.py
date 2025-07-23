import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

def main():
    if len(sys.argv) != 2:
        print("Usage: python fit_slope.py data.txt")
        sys.exit(1)

    filename = sys.argv[1]
    data = np.loadtxt(filename, skiprows=1)
    x = data[:, 1]
    y = data[:, 2]

    plt.plot(x, y, label='Full data', color='gray', alpha=0.6)

    try:
        x_start = float(input("Enter start of x-range for fitting: "))
        x_end = float(input("Enter end of x-range for fitting: "))
    except ValueError:
        print("Invalid input. Please enter numeric values.")
        sys.exit(1)

    mask = (x >= x_start) & (x <= x_end)
    x_fit = x[mask]
    y_fit = y[mask]

    if len(x_fit) < 2:
        print("Not enough points in selected range for fitting.")
        sys.exit(1)

    slope, intercept, r_value, p_value, std_err = linregress(x_fit, y_fit)
    Diff = slope / 60000

    y_line = slope * x_fit + intercept
    plt.plot(x_fit, y_line, 'r--', label=f'Fit: y = {slope:.4f}x + {intercept:.4f}')
    plt.xlabel("Column 2 (X)")
    plt.ylabel("Column 3 (Y)")
    plt.legend()
    plt.title("Linear Fit to Selected Range")
    plt.grid(True)
    plt.show()

    print(f"Slope of fitted line: {slope:.6f} (units of y/x)")
    print(f"Diffusivity Coefficient: {Diff:.3e} (units of cm^2/sec)")

if __name__ == "__main__":
    main()

