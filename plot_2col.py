import numpy as np
import matplotlib.pyplot as plt
import sys
import re

# -------------------------------
# Helper: expand shell-like column expressions
# -------------------------------
def expand_columns(expr, max_col):
    expr = expr.strip()
    if expr == "*":
        return list(range(1, max_col + 1))
    if expr.startswith("{") and expr.endswith("}"):
        return [int(x) for x in expr[1:-1].split(",")]
    if re.match(r"^\d+$", expr):
        return [int(expr)]
    if re.match(r"^\d+-\d+$", expr):
        start, end = map(int, expr.split("-"))
        return list(range(start, end + 1))
    return []

# -------------------------------
# CLI input
# -------------------------------
if len(sys.argv) < 2:
    print("Usage: python plot_columns.py <datafile1> <datafile2> ...")
    sys.exit(1)

# Detect columns
num_cols = None
with open(sys.argv[1], "r") as f:
    for line in f:
        if line.startswith("#") or line.startswith("@") or not line.strip():
            continue
        parts = line.replace(",", " ").split()
        num_cols = len(parts)
        break

if not num_cols or num_cols < 2:
    print(f"Error: Not enough numeric columns in {sys.argv[1]}")
    sys.exit(1)

print(f"Detected {num_cols} columns in {sys.argv[1]}.")

# -------------------------------
# Parse column pair specification
# -------------------------------
plot_input = input(
    "Enter column pairs to plot (e.g. 1-2, 1-*, *-1, *-*, 1-{2,3,4}): "
).replace(" ", "")
if not plot_input:
    plot_input = "1-2"

pairs = []
for pair in plot_input.split(","):
    if "-" not in pair:
        continue
    xexpr, yexpr = pair.split("-")
    xcols = expand_columns(xexpr, num_cols)
    ycols = expand_columns(yexpr, num_cols)
    for x in xcols:
        for y in ycols:
            if x != y:
                pairs.append((x, y))

pairs = sorted(set(pairs))
print(f"Preparing {len(pairs)} plots: {pairs}")

# -------------------------------
# Load all data files
# -------------------------------
all_data = {}
for filename in sys.argv[1:]:
    data = []
    try:
        with open(filename, "r") as f:
            for line in f:
                if line.startswith("#") or line.startswith("@") or not line.strip():
                    continue
                parts = line.replace(",", " ").split()
                try:
                    row = [float(x) for x in parts]
                    data.append(row)
                except ValueError:
                    continue
        data = np.array(data)
        if data.size == 0:
            print(f"⚠️ No valid data in {filename}. Skipping.")
            continue
        all_data[filename] = data
    except Exception as e:
        print(f"❌ Error reading {filename}: {e}")

if not all_data:
    print("No valid files loaded.")
    sys.exit(1)

# -------------------------------
# Plot each (x, y) pair separately
# -------------------------------
for (xcol, ycol) in pairs:
    print(f"\n🟩 Plot setup for Columns {xcol}-{ycol}")

    # Ask individually for labels/title
    xlabel = input(f"Enter X label for plot {xcol}-{ycol} (default: Column {xcol}): ").strip()
    ylabel = input(f"Enter Y label for plot {xcol}-{ycol} (default: Column {ycol}): ").strip()
    title = input(f"Enter title for plot {xcol}-{ycol} (default: Columns {xcol} vs {ycol}): ").strip()
    scale_choice = input(
        f"Scale for plot {xcol}-{ycol} (linear / loglog / semilogx / semilogy) [default: linear]: "
    ).strip().lower()
    if not scale_choice:
        scale_choice = "linear"

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 5))
    for fname, data in all_data.items():
        if xcol - 1 < data.shape[1] and ycol - 1 < data.shape[1]:
            ax.plot(data[:, xcol - 1], data[:, ycol - 1], label=fname)
        else:
            print(f"⚠️ Skipping {fname}: columns {xcol}-{ycol} out of range.")

    ax.set_xlabel(xlabel if xlabel else f"Column {xcol}")
    ax.set_ylabel(ylabel if ylabel else f"Column {ycol}")
    ax.set_title(title if title else f"Columns {xcol} vs {ycol}")
    ax.grid(True)
    ax.legend()

    # Apply scale
    if scale_choice == "loglog":
        ax.set_xscale("log")
        ax.set_yscale("log")
    elif scale_choice == "semilogx":
        ax.set_xscale("log")
    elif scale_choice == "semilogy":
        ax.set_yscale("log")

    fig.tight_layout()

plt.show()
