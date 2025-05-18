#!/bin/bash

# Check if GaussSum is installed
if ! command -v gausssum &> /dev/null; then
    echo "GaussSum is not installed or not found in your PATH."
    exit 1
fi

# Check if at least one log or out file exists in the current directory
files=$(find . -maxdepth 1 -type f \( -name "*.log" -o -name "*.out" \))
if [ -z "$files" ]; then
    echo "No log or out files found in the current directory."
    exit 1
fi

# Select a file to open
echo "Select a file to open:"
select file in $files; do
    if [ -n "$file" ]; then
        echo "Opening $file in GaussSum and navigating to orbitals section..."
        gausssum "$(realpath "$file")" --mo
        break
    else
        echo "Invalid selection. Please try again."
    fi
done