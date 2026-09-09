import pandas as pd
import matplotlib.pyplot as plt
import argparse

# --- Argument parsing ---
parser = argparse.ArgumentParser(description="Plot columns from a CSV file.")
parser.add_argument("csv_file", type=str, help="Path to the CSV file")
args = parser.parse_args()

# --- Load CSV ---
try:
    df = pd.read_csv(args.csv_file)
except Exception as e:
    print(f"Error reading CSV: {e}")
    exit(1)

# --- Show columns with numbers ---
print("\nAvailable columns:")
for idx, col in enumerate(df.columns):
    print(f"{idx}: {col}")

# --- Select columns for plotting ---
try:
    x_idx = int(input("\nEnter the number corresponding to the x-axis column: "))
    y_idx = int(input("Enter the number corresponding to the y-axis column: "))
except ValueError:
    print("Please enter valid integers for column numbers.")
    exit(1)

if not (0 <= x_idx < len(df.columns)) or not (0 <= y_idx < len(df.columns)):
    print("Invalid column numbers.")
    exit(1)

x_col = df.columns[x_idx]
y_col = df.columns[y_idx]

# --- Plot ---
plt.figure(figsize=(8, 5))
plt.plot(df[x_col], df[y_col], marker="o", linestyle="-", color="blue")
plt.xlabel(x_col)
plt.ylabel(y_col)
plt.title(f"{y_col} vs {x_col}")
plt.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()
plt.show()
