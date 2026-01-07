import argparse
import sys

import pandas as pd
import matplotlib.pyplot as plt


def parse_column_input(user_input, available_columns):
    """
    Parse a comma-separated list of column names and validate them.
    """
    columns = [col.strip() for col in user_input.split(",") if col.strip()]
    invalid = [col for col in columns if col not in available_columns]

    if invalid:
        raise ValueError(f"Invalid column(s): {', '.join(invalid)}")

    if not columns:
        raise ValueError("No columns selected.")

    return columns


def main():
    parser = argparse.ArgumentParser(description="Interactive CSV plotting tool")
    parser.add_argument("csv_file", help="Path to the CSV file")
    args = parser.parse_args()

    try:
        df = pd.read_csv(args.csv_file)
    except Exception as e:
        print(f"Failed to read CSV file: {e}")
        sys.exit(1)

    if df.empty:
        print("The CSV file is empty.")
        sys.exit(1)

    print("\nAvailable columns:")
    for col in df.columns:
        print(f"  - {col}")

    try:
        x_input = input(
            "\nEnter X column(s) (comma-separated): "
        )
        x_columns = parse_column_input(x_input, df.columns)

        y_input = input(
            "Enter Y column(s) (comma-separated): "
        )
        y_columns = parse_column_input(y_input, df.columns)

    except ValueError as e:
        print(f"Input error: {e}")
        sys.exit(1)

    # Plotting
    plt.figure()

    for x_col in x_columns:
        for y_col in y_columns:
            plt.plot(df[x_col], df[y_col], label=f"{y_col} vs {x_col}")

    plt.xlabel(", ".join(x_columns))
    plt.ylabel(", ".join(y_columns))
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
